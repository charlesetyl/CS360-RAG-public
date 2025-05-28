# src/sqlgen.py
from ollama import chat, ChatResponse

def answer_gen(textual_question, db_engine, model_name):

    # TODO

    # 데이터베이스의 스키마 정보를 가져옵니다.
    # get information from database schema
    schema = """
CREATE TABLE country( country_name  VARCHAR(30), trade_port    VARCHAR(30), development FLOAT, PRIMARY KEY (country_name));

CREATE TABLE trading_node(    trading_node    VARCHAR(30), local_value FLOAT,    node_inland BOOLEAN,    total_power FLOAT,    outgoing FLOAT,    ingoing FLOAT,   PRIMARY KEY (trading_node));

CREATE TABLE flow(    upstream    VARCHAR(30),    downstream VARCHAR(30),    flow FLOAT,   PRIMARY KEY (upstream, downstream));

CREATE TABLE node_country(    node_name     VARCHAR(30), country_name    VARCHAR(30),    is_home BOOLEAN, merchant BOOLEAN,    base_trading_power FLOAT,    calculated_trading_power FLOAT,   PRIMARY KEY (node_name, country_name));
    """
    
    # 모델에 전달할 프롬프트를 구성합니다.
    # configure model to deliver prompt?    
    prompt = (
        f"""
        Given the following database schema, generate a SQL query to answer the question.

        database schema: {schema}\n\n
        Question:\n{textual_question}\n\n

        Important Notes:
        - For questions asking "which" or "what", if there is more than one answer, use ORDER BY with DESC and LIMIT 1 to get the top result
        - For counting questions, use COUNT()
        - Always use proper SQL syntax with semicolon at the end
        - Return ONLY the SQL query, no explanations

        SQL query:
        
        """
    )
    
    # ollama의 chat API를 호출하여 모델로부터 응답을 받습니다.
    # use model to call ollama's chat API and receive a response
    response: ChatResponse = chat(model=model_name, options={'temperature': 0}, messages=[
        {
            'role': 'user',
            'content': prompt,
        }
    ])
    
    # 응답에서 SQL 쿼리를 추출합니다.
    # abstract the sql query from the response
    sql_query = response.message.content
    query_result = db_engine.query(sql_query)
    return query_result

