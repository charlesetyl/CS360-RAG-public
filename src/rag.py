from ollama import chat
from ollama.types import ChatResponse

def answer_gen(textual_question, db_engine, model_name):
    # Step 1: Embed your schema (for context)
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

    # Step 2: Compose a clean, focused prompt
    prompt = f"""
You are an expert SQL query generator.

Based on the schema below, write a valid SQL query that answers the user's question.
Only output a single SQL query — no explanations, no markdown, no commentary.

If multiple results are possible, use ORDER BY ... DESC LIMIT 1.

Schema:
{schema}

User question:
{textual_question}

SQL:
""".strip()

    # Step 3: Call the model
    response: ChatResponse = chat(model=model_name, options={'temperature': 0}, messages=[
        {"role": "user", "content": prompt}
    ])
    raw_sql = response.message.content.strip()

    # Step 4: Clean output (remove markdown, if any)
    if raw_sql.lower().startswith("```sql"):
        raw_sql = raw_sql.strip("`").split("\n", 1)[1].rsplit("```", 1)[0].strip()

    print("[DEBUG] Generated SQL:", raw_sql)

    # Step 5: Run SQL on your engine
    try:
        query_result = db_engine.query(raw_sql)
    except Exception as e:
        return f"[ERROR] Could not run SQL: {e}"

    return query_result
