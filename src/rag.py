from ollama import chat, ChatResponse  
from sqlalchemy import text  

def answer_gen(textual_question, db_engine, model_name):   
    
    # 데이터베이스의 스키마 정보를 가져옵니다.
    schema = """
CREATE TABLE country( country_name  VARCHAR(30), trade_port    VARCHAR(30), development FLOAT, PRIMARY KEY (country_name));

CREATE TABLE trading_node(    trading_node    VARCHAR(30), local_value FLOAT,    node_inland BOOLEAN,    total_power FLOAT,    outgoing FLOAT,    ingoing FLOAT,   PRIMARY KEY (trading_node));

CREATE TABLE flow(    upstream    VARCHAR(30),    downstream VARCHAR(30),    flow FLOAT,   PRIMARY KEY (upstream, downstream));

CREATE TABLE node_country(    node_name     VARCHAR(30), country_name    VARCHAR(30),    is_home BOOLEAN, merchant BOOLEAN,    base_trading_power FLOAT,    calculated_trading_power FLOAT,   PRIMARY KEY (node_name, country_name));
    """

    # 모델에 전달할 프롬프트를 구성합니다.
    # prompt structure: 1. identity, 2. instructions, 3. examples
    prompt = f"""
    
    You are a MySQL query writer.

    Given the following database schema, generate a single line SQL query to answer the question.

    Instructions:
    - Use SELECT statements only.
    - ONLY return the SQL query, NOT explanations, markdown, or text
    - If multiple rows are returned, always ORDER BY the answer DESC LIMIT 1.

    # schema: {schema}

    # Examples:

    Question: How many nodes are inland?
    Answer: SELECT COUNT(*) FROM trading_node WHERE node_inland = TRUE;

    Question: Which node is connected as the upstream of the highest flow?
    Answer: SELECT upstream FROM flow ORDER BY flow DESC LIMIT 1;

    Question: How many countries are there?
    Answer: SELECT COUNT(*) FROM country;

    Question: Which country has the lexicographically last name?
    Answer: SELECT country_name FROM country ORDER BY country_name DESC LIMIT 1;


    Question: {textual_question}
    Answer:"""


    try:
        # ollama의 chat API를 호출하여 모델로부터 응답을 받습니다.
        response: ChatResponse = chat( model=model_name, options={"temperature": 0}, messages=[
            {
                'role': 'user',
                'content': prompt}],
        )

        # 응답에서 SQL 쿼리를 추출합니다.
        sql_query = (
            response.message.content
            .replace("```sql", "")
            .replace("```", "")
            .replace("= 1", "= TRUE")
            .replace("= 0", "= FALSE")
            .strip()
        )

        try:
            result = db_engine._engine.connect().execute(text(sql_query))
            row = result.fetchone()

            if row is None:
                return None

            value = row[0]

            if isinstance(value, int):
                return value
            elif isinstance(value, float):
                return round(value, 2)
            elif isinstance(value, int):
                return str(value).strip()
            else:
                return str(value).strip()
        except Exception:
             return None
        
    except Exception:
        return None
