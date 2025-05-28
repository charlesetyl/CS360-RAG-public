from ollama import chat, ChatResponse
import sqlparse
import re

def is_valid_sql(sql: str) -> bool:
    return sql.lstrip().lower().startswith(("select", "with"))

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

    base_prompt = (
        f"You are a SQL query generator. "
        f"Given a schema and a question, generate only a valid SQL query. "
        f"No explanations, no markdown. Use ORDER BY ... DESC LIMIT 1 if multiple answers.\n\n"
        f"Schema:\n{schema}\n\n"
        f"Question:\n{textual_question}\n\n"
        f"SQL:"
    )

    for _ in range(3):  # Try up to 3 times
        response: ChatResponse = chat(
            model=model_name,
            options={'temperature': 0},
            messages=[{'role': 'user', 'content': base_prompt}]
        )

        raw_output = response.message.content.strip()
        sql_query = re.sub(r"```sql|```", "", raw_output).strip()
        sql_query = sqlparse.format(sql_query, strip_comments=True).strip()

        if is_valid_sql(sql_query):
            try:
                result = db_engine.query(sql_query)
                if not result:
                    return None
                return result[0][0]  # Return the first column of the first row
            except Exception as e:
                return f"SQL Execution Error: {e}"

    return "Failed to generate valid SQL after 3 attempts."
