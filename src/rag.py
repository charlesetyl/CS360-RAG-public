from ollama import chat, ChatResponse
from sqlalchemy import text

def answer_gen(textual_question: str, db_engine, model_name: str) -> str:   
    # TODO

    # 데이터베이스의 스키마 정보를 가져옵니다.
    schema = """
CREATE TABLE country( country_name  VARCHAR(30), trade_port    VARCHAR(30), development FLOAT, PRIMARY KEY (country_name));

CREATE TABLE trading_node(    trading_node    VARCHAR(30), local_value FLOAT,    node_inland BOOLEAN,    total_power FLOAT,    outgoing FLOAT,    ingoing FLOAT,   PRIMARY KEY (trading_node));

CREATE TABLE flow(    upstream    VARCHAR(30),    downstream VARCHAR(30),    flow FLOAT,   PRIMARY KEY (upstream, downstream));

CREATE TABLE node_country(    node_name     VARCHAR(30), country_name    VARCHAR(30),    is_home BOOLEAN, merchant BOOLEAN,    base_trading_power FLOAT,    calculated_trading_power FLOAT,   PRIMARY KEY (node_name, country_name));
    """
    
    # Prompt Creation --> 1 FULL STRING for the LLM with your conditions, example questions and expected output

    # The {schema} part --> think of it as giving your LLM a cheatsheet
    # LLMs don't have memory of your database. You must tell it what tables exist and what columns they have.
    # This allows the LLM to:
    # 1. Understand relationships (like foreign keys)
    # 2. Use the correct tables and column names
    # 3. Avoid hallucinating data structures


    prompt = f"""
    You are an expert MySQL query writer.

    Your job is to write a single-line SQL query that directly answers the question using the schema.

    ## IMPORTANT:
    - Use SELECT statements only.
    - Do NOT include explanations, markdown, or text — only return the SQL query.
    - If multiple rows are returned, always ORDER BY the answer DESC LIMIT 1.
    - Assume booleans use TRUE/FALSE, not 1/0.
    - Use proper joins when needed.

    ## Schema:
    {schema}

    ## Examples:
    Q: How many countries are there?
    A: SELECT COUNT(*) FROM country;

    Q: What is the most powerful inland node?
    A: SELECT trading_node FROM trading_node WHERE node_inland = TRUE ORDER BY total_power DESC LIMIT 1;

    Q: How many nodes are inland?
    A: SELECT COUNT(*) FROM trading_node WHERE node_inland = TRUE;

    Q: Which country has the lexicographically last name?
    A: SELECT country_name FROM country ORDER BY country_name DESC LIMIT 1;

    Q: {textual_question}
    A:"""

    # temperature : 0 --> no randomness
    # higher the temperature, the more the model samples from a wider range of possibilities
    # there will be more variety in anwers which is NOT good because we are generating SQL queries
    # precision and accuracy is important or the wrong things will be queried
    try:
        response: ChatResponse = chat(
            model=model_name,
            options={"temperature": 0},
            messages=[{"role": "user", "content": prompt}],
        )

    # This part cleans the SQl so theres no markdown syntax, and correct mySQL formatting for booleans
        sql_query = response.message.content.strip()
        print("\n================== LLM GENERATED SQL ==================")
        print(sql_query)
        print("=======================================================\n")
        sql_query = sql_query.replace("```sql", "").replace("```", "").strip()
        sql_query = sql_query.replace("= 1", "= TRUE").replace("= 0", "= FALSE")

        # This part adds the ORDER BY and LIMIT if needed
        if "GROUP BY" in sql_query and "ORDER BY" not in sql_query:
            sql_query += " ORDER BY COUNT(*) DESC LIMIT 1"
        elif (
            "SELECT COUNT" not in sql_query
            and "SELECT SUM" not in sql_query
            and "SELECT AVG" not in sql_query
            and "SELECT MIN" not in sql_query
            and "SELECT MAX" not in sql_query
            and "ORDER BY" not in sql_query
            and "LIMIT" not in sql_query
        ):
            sql_query += " ORDER BY 1 DESC LIMIT 1"

        # This part executes the SQL query --> after the LLM generates the query based on
        # your Natural Language Question, this part executes the query and returns you the answer
            try:
                with db_engine._engine.connect() as conn:
                    result = conn.execute(text(sql_query))
                    row = result.fetchone()
                    #DEBUG
                    print("[DEBUG] Raw DB row:", row)

                if row is None or len(row) == 0:
                    return None

                value = row[0]

                # This part converts the value to the correct type
                if isinstance(value, str) and value.replace(".", "", 1).isdigit():
                    value = float(value)

                if isinstance(value, float) and value.is_integer():
                    return int(value)
                elif isinstance(value, float):
                    return round(value, 2)
                elif isinstance(value, int):
                    return value
                else:
                    return str(value).strip()

            except Exception as e:
                #DEBUG
                print("[ERROR]", e)
                return None

    # Global error handling because
    except Exception:
        return None