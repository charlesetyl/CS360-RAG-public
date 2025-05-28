# src/sqlgen.py
from ollama import chat, ChatResponse
import sqlparse

def answer_gen(textual_question, db_engine, model_name):
    # Database schema provided to the model
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

    # Create prompt for the model
    prompt = (
        f"You are an AI that generates SQL queries based on a database schema and a natural language question.\n"
        f"Schema:\n{schema}\n\n"
        f"Question:\n{textual_question}\n\n"
        f"Return ONLY the SQL query needed to answer the question."
    )

    # Call the model
    response: ChatResponse = chat(model=model_name, messages=[
        {
            'role': 'user',
            'content': prompt,
        }
    ])

    # Extract and clean the SQL query from the model's output
    sql_query = response.message.content.strip()
    # Optional: format or validate query (e.g. remove markdown formatting or language tags)
    if sql_query.lower().startswith("```sql"):
        sql_query = sql_query.strip("`").split("\n", 1)[1].rsplit("```", 1)[0].strip()

    # Optionally, format the query nicely (not required for execution)
    sql_query = sqlparse.format(sql_query, strip_comments=True).strip()

    # Execute the SQL query and return the result
    try:
        query_result = db_engine.query(sql_query)
    except Exception as e:
        query_result = f"Error executing SQL query: {e}"

    return query_result
