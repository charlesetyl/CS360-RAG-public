from ollama import chat, ChatResponse
import re
import pandas as pd

def answer_gen(textual_question, db_engine, model_name):
    """
    Generate answers using RAG system with LLM-generated SQL queries
    """
    
    # Database schema information
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
    
    # Enhanced prompt with examples and clear instructions
    prompt = f"""Given the following database schema, generate a SQL query to answer the question.

Database Schema:
{schema}

Important Notes:
- For questions asking "which" or "what", use ORDER BY with DESC and LIMIT 1 to get the top result
- For counting questions, use COUNT()
- Boolean values: TRUE for inland nodes, FALSE for non-inland nodes
- Always use proper SQL syntax with semicolon at the end
- Return only the SQL query, no explanations

Question: {textual_question}

SQL Query:"""
    
    # Generate SQL query using LLM with temperature=0 for consistency
    try:
        response: ChatResponse = chat(
            model=model_name, 
            options={'temperature': 0}, 
            messages=[{
                'role': 'user',
                'content': prompt,
            }]
        )
        
        # Extract and clean the SQL query
        sql_query = response.message.content.strip()
        sql_query = clean_sql_query(sql_query)
        
        # Execute the query and process results
        query_result = db_engine.query(sql_query)
        
        # Post-process the result based on the question type
        final_answer = post_process_result(query_result, textual_question)
        
        return final_answer
        
    except Exception as e:
        # Fallback: try a simpler approach if the first attempt fails
        try:
            simple_prompt = f"""Schema: {schema}
Question: {textual_question}
Generate SQL query:"""
            
            response: ChatResponse = chat(
                model=model_name, 
                options={'temperature': 0}, 
                messages=[{
                    'role': 'user',
                    'content': simple_prompt,
                }]
            )
            
            sql_query = clean_sql_query(response.message.content.strip())
            query_result = db_engine.query(sql_query)
            return post_process_result(query_result, textual_question)
            
        except Exception:
            # Return empty result if all attempts fail
            return pd.DataFrame()

def clean_sql_query(sql_query):
    """
    Clean and validate the generated SQL query
    """
    # Remove markdown code blocks if present
    sql_query = re.sub(r'```sql\s*', '', sql_query)
    sql_query = re.sub(r'```\s*', '', sql_query)
    
    # Remove extra whitespace and newlines
    sql_query = ' '.join(sql_query.split())
    
    # Ensure query ends with semicolon
    if not sql_query.endswith(';'):
        sql_query += ';'
    
    # Fix common issues
    sql_query = sql_query.replace('`', '')  # Remove backticks
    
    return sql_query

def post_process_result(query_result, question):
    """
    Post-process query results based on question requirements
    """
    if query_result is None or query_result.empty:
        return query_result
    
    # Handle single value results
    if query_result.shape == (1, 1):
        value = query_result.iloc[0, 0]
        
        # Round decimal numbers to 2 decimal places
        if isinstance(value, float):
            return round(value, 2)
        
        # Convert to appropriate type
        if isinstance(value, str):
            return value.lower().strip()  # Normalize string case
        
        return value
    
    # Handle multiple results - apply ORDER BY logic as specified
    if len(query_result) > 1:
        # For multiple answers, select by ORDER BY {answer} DESC LIMIT 1
        if query_result.shape[1] == 1:  # Single column
            col_name = query_result.columns[0]
            
            # Sort by the column in descending order
            sorted_result = query_result.sort_values(by=col_name, ascending=False)
            value = sorted_result.iloc[0, 0]
            
            # Apply formatting
            if isinstance(value, float):
                return round(value, 2)
            elif isinstance(value, str):
                return value.lower().strip()
            
            return value
    
    # Handle counting results (should be single integer)
    if 'count' in str(query_result.columns).lower():
        return int(query_result.iloc[0, 0])
    
    # Default: return the first value of the first row
    value = query_result.iloc[0, 0]
    if isinstance(value, float):
        return round(value, 2)
    elif isinstance(value, str):
        return value.lower().strip()
    
    return value