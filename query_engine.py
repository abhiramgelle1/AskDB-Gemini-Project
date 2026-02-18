from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_community.utilities.sql_database import SQLDatabase
try:
    from langchain_core.globals import set_llm_cache
    from langchain_core.caches import InMemoryCache
    set_llm_cache(InMemoryCache())
except Exception:
    try:
        from langchain.globals import set_llm_cache
        from langchain.cache import InMemoryCache
        set_llm_cache(InMemoryCache())
    except Exception:
        pass  # caching optional
import os
import re
import warnings
# Suppress SQLAlchemy cycle warning (e.g. user_roles/users FK); harmless for query generation
warnings.filterwarnings("ignore", message=".*Cannot correctly sort tables.*unresolvable cycles.*", category=Warning)
try:
    from langchain.chains import create_sql_query_chain
except ModuleNotFoundError:
    from langchain_classic.chains import create_sql_query_chain
from langchain_google_genai import ChatGoogleGenerativeAI  # Replace with actual Google Gemini module
from langchain_community.tools import QuerySQLDatabaseTool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder,FewShotChatMessagePromptTemplate,PromptTemplate
from langchain_chroma import Chroma
from langchain_core.example_selectors import SemanticSimilarityExampleSelector
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from operator import itemgetter
from pydantic import BaseModel, Field
from typing import List
import pandas as pd
from dotenv import load_dotenv

# Enable in-memory caching for LLM responses (optional)

# Import prompts configuration
from prompts_config import (
    SQL_GENERATION_PROMPT,
    TABLE_SELECTION_PROMPT,
    ANSWER_GENERATION_PROMPT,
    FEW_SHOT_EXAMPLES
)

# Load environment variables from .env file
load_dotenv()

# Database configuration from environment variables (PostgreSQL ogms)
db_type = os.getenv("DB_TYPE", "postgresql")
db_user = os.getenv("DB_USER", "postgres")
db_password = os.getenv("DB_PASSWORD", "")
db_host = os.getenv("DB_HOST", "localhost")
db_port = os.getenv("DB_PORT", "5432")
db_name = os.getenv("DB_NAME", "ogms")

# Construct database URI based on type
if db_type.lower() == "sqlite":
    database_uri = f"sqlite:///{db_name}"
    print(f"🔌 Attempting to connect to SQLite database: {db_name}")
elif db_type.lower() == "postgresql":
    # URL encode the password to handle special characters
    from urllib.parse import quote_plus
    encoded_password = quote_plus(db_password) if db_password else ""
    database_uri = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    print(f"🔌 Attempting to connect to PostgreSQL database at: {db_host}:{db_port}/{db_name}")
else:
    # URL encode the password to handle special characters
    from urllib.parse import quote_plus
    encoded_password = quote_plus(db_password) if db_password else ""
    database_uri = f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    print(f"🔌 Attempting to connect to MySQL database at: {db_host}:{db_port}/{db_name}")

try:
    db = SQLDatabase.from_uri(database_uri)
    print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    print("\n📝 Please configure your database in .env file:")
    if db_type.lower() == "sqlite":
        print("   - DB_NAME=your_database_file.db")
    else:
        print("   - DB_HOST=your_cloud_sql_ip")
        print("   - DB_USER=your_username")
        print("   - DB_PASSWORD=your_password")
        print("   - DB_NAME=your_database")
    raise

# Set API keys from environment variables
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY", "")

# LangChain/LangSmith Configuration
os.environ["LANGCHAIN_TRACING_V2"] = os.getenv("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "askdb_project")
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY", "")

# Optional: Set custom LangChain endpoint (default is https://api.smith.langchain.com)
langchain_endpoint = os.getenv("LANGCHAIN_ENDPOINT")
if langchain_endpoint:
    os.environ["LANGCHAIN_ENDPOINT"] = langchain_endpoint
    print(f"🔗 Using custom LangChain endpoint: {langchain_endpoint}")

# Check if LangChain tracing is enabled
if os.environ["LANGCHAIN_TRACING_V2"].lower() == "true":
    print(f"📊 LangChain tracing enabled - Project: {os.environ['LANGCHAIN_PROJECT']}")
else:
    print("📊 LangChain tracing disabled")

# Initialize Google Gemini LLM (GEMINI_MODEL in .env; gemini-2.0-flash works, gemini-3-flash-preview if quota)
_gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
_llm_timeout = int(os.getenv("GEMINI_TIMEOUT", "90"))  # Default 90s for complex queries
llm = ChatGoogleGenerativeAI(
    model=_gemini_model,
    temperature=0,
    max_retries=3,  # Increased retries for timeout recovery
    timeout=_llm_timeout
)
print(f"✅ Google Gemini LLM initialized: {_gemini_model}")




def clean_sql_query(text: str) -> str:
    """
    Clean SQL query by removing code block syntax, various SQL tags, backticks,
    prefixes, and unnecessary whitespace while preserving the core SQL query.

    Args:
        text (str): Raw SQL query text that may contain code blocks, tags, and backticks

    Returns:
        str: Cleaned SQL query
    """
    # Step 1: Remove code block syntax and any SQL-related tags
    # This handles variations like ```sql, ```SQL, ```SQLQuery, etc.
    block_pattern = r"```(?:sql|SQL|SQLQuery|mysql|postgresql)?\s*(.*?)\s*```"
    text = re.sub(block_pattern, r"\1", text, flags=re.DOTALL)

    # Step 2: Handle "SQLQuery:" prefix and similar variations
    # This will match patterns like "SQLQuery:", "SQL Query:", "MySQL:", etc.
    prefix_pattern = r"^(?:SQL\s*Query|SQLQuery|MySQL|PostgreSQL|SQL)\s*:\s*"
    text = re.sub(prefix_pattern, "", text, flags=re.IGNORECASE)

    # Step 3: Extract the first SQL statement if there's random text after it
    # Look for a complete SQL statement ending with semicolon
    sql_statement_pattern = r"(SELECT.*?;)"
    sql_match = re.search(sql_statement_pattern, text, flags=re.IGNORECASE | re.DOTALL)
    if sql_match:
        text = sql_match.group(1)

    # Step 4: Remove backticks around identifiers
    text = re.sub(r'`([^`]*)`', r'\1', text)

    # Step 5: Normalize whitespace
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)

    # Step 6: Preserve newlines for main SQL keywords to maintain readability
    keywords = ['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'HAVING', 'ORDER BY',
               'LIMIT', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN',
               'OUTER JOIN', 'UNION', 'VALUES', 'INSERT', 'UPDATE', 'DELETE']

    # Case-insensitive replacement for keywords
    pattern = '|'.join(r'\b{}\b'.format(k) for k in keywords)
    text = re.sub(f'({pattern})', r'\n\1', text, flags=re.IGNORECASE)

    # Step 7: Final cleanup
    # Remove leading/trailing whitespace and extra newlines
    text = text.strip()
    text = re.sub(r'\n\s*\n', '\n', text)

    return text


execute_query = QuerySQLDatabaseTool(db=db)





# Load answer generation prompt from config
answer_prompt = PromptTemplate.from_template(ANSWER_GENERATION_PROMPT)

# Create a simple wrapper to format the answer
def format_answer(input_dict: dict) -> str:
    """Format the answer by invoking the prompt with the result"""
    question = input_dict.get("question", "")
    result = input_dict.get("result", "")
    
    # Debug: print what we're receiving
    print(f"🔍 Debug format_answer - question: {question[:50]}...")
    print(f"🔍 Debug format_answer - result type: {type(result)}, length: {len(str(result)) if result else 0}")
    
    # If result is empty, provide a default message
    if not result or result.strip() == "":
        result = "No data returned from the database query."
    
    # Format the prompt message
    message = ANSWER_GENERATION_PROMPT.format(question=question, result=result)
    
    # Get LLM response - create a message object (with timeout handling)
    from langchain_core.messages import HumanMessage
    try:
        response = llm.invoke([HumanMessage(content=message)])
    except Exception as e:
        error_str = str(e)
        if "DEADLINE_EXCEEDED" in error_str or "timeout" in error_str.lower() or "504" in error_str:
            return f"The query took too long to process. The database query returned: {result}. Please try rephrasing your question or breaking it into smaller parts."
        raise  # Re-raise other errors
    
    # Extract content (always return a string for the API/frontend)
    if isinstance(response, str):
        return response
    if hasattr(response, 'content'):
        content = response.content
        if isinstance(content, str):
            return content
        if isinstance(content, dict) and content.get("text"):
            return content["text"]
        if isinstance(content, list) and content:
            part = content[0]
            if isinstance(part, dict) and part.get("text"):
                return part["text"]
            return getattr(part, 'text', part) if hasattr(part, 'text') else str(part)
        return str(content) if content is not None else "No response."
    if isinstance(response, dict) and response.get("text"):
        return response["text"]
    return str(response)

rephrase_answer = RunnableLambda(format_answer)

# Load examples from config
examples = FEW_SHOT_EXAMPLES



example_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{input}\nSQLQuery:"),
        ("ai", "{query}"),
    ]
)
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
    input_variables=["input"],
)



# Temporarily disable semantic similarity due to API quota limits
# Use simple few-shot prompt without selector
few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=examples,
    input_variables=["input"],
)



def get_table_details():
    # Read the CSV file into a DataFrame
    table_description = pd.read_csv("database_table_descriptions.csv")
    table_docs = []

    # Iterate over the DataFrame rows to create Document objects
    table_details = ""
    for index, row in table_description.iterrows():
        table_details = table_details + "Table Name:" + row['table_name'] + "\n" + "Table Description:" + row['description'] + "\n\n"

    return table_details


class Table(BaseModel):
    """Table in SQL database."""

    name: List[str] = Field(description="List of Name of tables in SQL database.")

# table_names = "\n".join(db.get_usable_table_names())
table_details = get_table_details()
if "_RUN_FIRST" in table_details:
    print("⚠️  Run: python generate_table_descriptions.py — then edit database_table_descriptions.csv with your ogms table descriptions.")

# Load table selection prompt from config
table_details_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", TABLE_SELECTION_PROMPT),
            ("human", "{question}")
        ]
    )

structured_llm = llm.with_structured_output(Table)

table_chain = table_details_prompt | structured_llm



def get_tables(table_response: Table) -> List[str]:
    """
    Extracts the list of table names from a Table object.

    Args:
        table_response (Table): A Pydantic Table object containing table names.

    Returns:
        List[str]: A list of table names.
    """
    return table_response.name


select_table = {"question": itemgetter("question"), "table_details": itemgetter("table_details")} | table_chain | get_tables



# Load SQL generation prompt from config
final_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SQL_GENERATION_PROMPT),
        few_shot_prompt,
        ("human", "{input}"),
    ]
)


# from langchain_community.chat_message_histories import ChatMessageHistory
# history = ChatMessageHistory()

generate_query = create_sql_query_chain(llm, db,final_prompt)

chain = (
RunnablePassthrough.assign(table_names_to_use=select_table) |
RunnablePassthrough.assign(query=generate_query | RunnableLambda(clean_sql_query)).assign(
    result=itemgetter("query") | execute_query
)
| rephrase_answer
)


def execute_query_with_retry(inputs: dict) -> dict:
    """
    Custom LangChain runnable that executes SQL with retry logic.
    This keeps everything in a single trace.
    
    Args:
        inputs: Dict with 'query', 'question', 'table_details'
    
    Returns:
        Dict with 'result' or 'error'
    """
    sql_query = inputs.get("query")
    question = inputs.get("question")
    max_retries = 2
    attempt = 0
    
    print(f"📝 Executing query: {sql_query}")
    
    while attempt < max_retries:
        try:
            result = execute_query.invoke(sql_query)
            print(f"✅ Query executed successfully on attempt {attempt + 1}")
            # Format result as string for the LLM prompt
            if isinstance(result, list):
                if len(result) == 0:
                    result_str = "No records found in the database."
                else:
                    result_str = str(result)
            elif result is None:
                result_str = "No records found in the database."
            else:
                result_str = str(result)
            
            print(f"📊 Query result: {result_str[:200]}...")  # Debug: show first 200 chars
            return {**inputs, "result": result_str, "query": sql_query, "error": None}
        except Exception as e:
            error_message = str(e)
            print(f"⚠️ Query execution failed (attempt {attempt + 1}): {error_message}")
            attempt += 1
            
            if attempt < max_retries:
                print(f"🔄 Attempting to correct query...")
                # Correct the query using LLM
                correction_prompt = f"""You are a SQL expert. The following query failed with an error. Analyze the error and provide a CORRECTED query.

Original Question: {question}

Failed Query:
{sql_query}

Error Message:
{error_message}

Common Issues to Check:
1. Column doesn't exist - verify column names match the schema
2. Table doesn't exist - check table names are correct
3. Syntax errors - fix SQL syntax
4. Type mismatches - ensure correct data types
5. deleted_status on wrong table - only use on cases, orders, tasks, student_programs, programs (NOT contacts or payments)

Provide ONLY the corrected SQL query, no explanations:"""
                
                try:
                    corrected = llm.invoke(correction_prompt)
                    sql_query = clean_sql_query(corrected.content if hasattr(corrected, 'content') else str(corrected))
                    print(f"🔧 Corrected query: {sql_query}")
                    inputs["query"] = sql_query  # Update the query for next attempt
                except Exception as correction_error:
                    error_str = str(correction_error)
                    if "DEADLINE_EXCEEDED" in error_str or "timeout" in error_str.lower() or "504" in error_str:
                        print(f"⏱️ Query correction timed out. Using original query.")
                        break  # Don't retry if correction itself times out
                    print(f"❌ Error during correction: {correction_error}")
                    break
            else:
                print(f"❌ All retry attempts exhausted")
                # Return error in a format the answer chain can handle
                error_response = f"""Query execution failed after {max_retries} attempts.

Error: {error_message}

Query attempted: 
{sql_query}

This might be because:
- The column or table doesn't exist in the database
- There's a mismatch in the schema  
- The query syntax needs adjustment"""
                return {**inputs, "result": error_response, "query": sql_query, "error": error_message}
    
    return {**inputs, "result": "Unable to process the query", "query": sql_query if 'sql_query' in locals() else "N/A", "error": "Max retries reached"}


# Create the chain with retry logic integrated
chain = (
    RunnablePassthrough.assign(table_names_to_use=select_table) |
    RunnablePassthrough.assign(query=generate_query | RunnableLambda(clean_sql_query)) |
    RunnableLambda(execute_query_with_retry) |  # Custom retry logic here
    rephrase_answer
)


# Optimized chain without table selection (faster for simple queries)
# This skips 1 LLM call and reduces latency by ~30%
def is_simple_query(question: str) -> bool:
    """Detect if query is simple enough to skip table selection"""
    simple_keywords = ['count', 'total', 'how many', 'show', 'list', 'all']
    return any(keyword in question.lower() for keyword in simple_keywords)


def chain_code(q, m=None):
    """
    Execute the SQL chain to answer a question.
    Now with integrated retry logic in a single LangChain trace.
    
    Args:
        q (str): The user's question
        m (list, optional): Message history for context
    
    Returns:
        str: The AI's response
    """
    if m is None:
        m = []
    
    print(f"🤖 Processing question: {q}")
    
    # For simple queries, skip table selection to save ~30% latency
    if is_simple_query(q):
        print("⚡ Using fast path (skipping table selection)")
        fast_chain = (
            RunnablePassthrough.assign(query=generate_query | RunnableLambda(clean_sql_query)) |
            RunnableLambda(execute_query_with_retry) |
            rephrase_answer
        )
        response = fast_chain.invoke({"question": q, "messages": m, "table_details": table_details})
    else:
        response = chain.invoke({"question": q, "messages": m, "table_details": table_details})
    
    return response

