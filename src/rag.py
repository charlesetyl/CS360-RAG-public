# src/sqlgen.py
from ollama import chat, ChatResponse

def answer_gen(textual_question, db_engine, model_name):

    # TODO

    # 데이터베이스의 스키마 정보를 가져옵니다.
    schema = """
CREATE TABLE country( country_name  VARCHAR(30), trade_port    VARCHAR(30), development FLOAT, PRIMARY KEY (country_name));

CREATE TABLE trading_node(    trading_node    VARCHAR(30), local_value FLOAT,    node_inland BOOLEAN,    total_power FLOAT,    outgoing FLOAT,    ingoing FLOAT,   PRIMARY KEY (trading_node));

CREATE TABLE flow(    upstream    VARCHAR(30),    downstream VARCHAR(30),    flow FLOAT,   PRIMARY KEY (upstream, downstream));

CREATE TABLE node_country(    node_name     VARCHAR(30), country_name    VARCHAR(30),    is_home BOOLEAN, merchant BOOLEAN,    base_trading_power FLOAT,    calculated_trading_power FLOAT,   PRIMARY KEY (node_name, country_name));
    """
    
    # 모델에 전달할 프롬프트를 구성합니다.
    prompt = (
        f"You are a SQL query generator. "
        f"Given a schema and a natural language question, generate a valid SQL query. "
        f"Return ONLY the SQL query without explanations or formatting. "
        f"Use 'ORDER BY ... DESC LIMIT 1' for multiple possible answers.\n\n"
        f"Schema:\n{schema}\n\n"
        f"Question:\n{textual_question}\n\n"
        f"SQL:"
    )
    
    # ollama의 chat API를 호출하여 모델로부터 응답을 받습니다.
    response: ChatResponse = chat(model=model_name, options={'temperature': 0}, messages=[
        {
            'role': 'user',
            'content': prompt,
        }
    ])
    
    # 응답에서 SQL 쿼리를 추출합니다.
    # Get and clean the raw SQL string
    sql_query = response.message.content.strip()

    # Remove surrounding markdown or language tags
    if sql_query.lower().startswith("```sql") or sql_query.lower().startswith("```"):
        sql_query = sql_query.strip("`").split("\n", 1)[1].rsplit("```", 1)[0].strip()

    # Final cleanup: remove lingering semicolons or invalid characters
    sql_query = sql_query.rstrip(';')

    try:
        # Execute SQL and get result
        query_result = db_engine.query(sql_query)
    except Exception as e:
        return f"Error executing SQL query: {e}"

    return query_result

    # sql_query = response.message.content
    # query_result = db_engine.query(sql_query)
    # return query_result