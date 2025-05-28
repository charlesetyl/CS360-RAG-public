# src/sqlgen.py
from ollama import chat, ChatResponse
import sqlparse
import re

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
        f"\nSchema:\n{schema}\n"
        f"\nQuestion:\n{textual_question}\n"
        f"\nSQL:"
    )

    response: ChatResponse = chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt,
        }
    ])

    # Extract clean SQL query from response
    raw_output = response.message.content.strip()

    # Remove markdown code fences if present
    sql_query = re.sub(r"```sql|```", "", raw_output).strip()

    # Optionally format it for clarity (not required)
    sql_query = sqlparse.format(sql_query, strip_comments=True).strip()

    try:
        query_result = db_engine.query(sql_query)
    except Exception as e:
        query_result = f"Error executing SQL query: {e}"

    return query_result
