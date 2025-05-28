# src/rag.py
from ollama import chat, ChatResponse
import sqlparse
import re
import pandas as pd

def answer_gen(textual_question, db_engine, model_name):
    schema = """
CREATE TABLE country(
    country_name VARCHAR(30),
    trade_port VARCHAR(30),
    development FLOAT,
    PRIMARY KEY (country_name)
);

CREATE TABLE trading_node(
    trading_node VARCHAR(30),
    local_value FLOAT,
    node_inland BOOLEAN,
    total_power FLOAT,
    outgoing FLOAT,
    ingoing FLOAT,
    PRIMARY KEY (trading_node)
);

CREATE TABLE flow(
    upstream VARCHAR(30),
    downstream VARCHAR(30),
    flow FLOAT,
    PRIMARY KEY (upstream, downstream)
);

CREATE TABLE node_country(
    node_name VARCHAR(30),
    country_name VARCHAR(30),
    is_home BOOLEAN,
    merchant BOOLEAN,
    base_trading_power FLOAT,
    calculated_trading_power FLOAT,
    PRIMARY KEY (node_name, country_name)
);
    """

    prompt = (
        f"You are a SQL expert. Based on the following schema and natural language question, generate ONLY the correct SQL query.\n"
        f"DO NOT provide explanations, comments, or markdown formatting.\n"
        f"Make sure to use 'ORDER BY ... DESC LIMIT 1' if multiple results are possible.\n"
        f"Schema:\n{schema}\n"
        f"Question:\n{textual_question}\n"
        f"SQL:"
    )

    response: ChatResponse = chat(model=model_name, options={'temperature': 0}, messages=[
        {
            'role': 'user',
            'content': prompt,
        }
    ])

    raw_output = response.message.content.strip()
    sql_query = re.sub(r"```sql|```", "", raw_output).strip()
    sql_query = sqlparse.format(sql_query, strip_comments=True).strip()

    try:
        query_result = db_engine.query(sql_query)
    except Exception as e:
        return f"SQL Execution Error: {e}"

    if not query_result or len(query_result) == 0:
        return None

    # Convert result to DataFrame for easier processing
    df = pd.DataFrame(query_result)

    if df.empty or df.shape[1] == 0:
        return None

    value = df.iloc[0, 0]

    # Post-process result
    if isinstance(value, float):
        return round(value, 2)
    elif isinstance(value, (int, bool)):
        return value
    elif isinstance(value, str):
        return value.strip()
    else:
        return str(value)
