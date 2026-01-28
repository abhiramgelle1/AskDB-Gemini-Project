import os
import re
import json
import sqlite3
import time
from typing import Optional
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, render_template_string, session
from flask_cors import CORS

# Google Generative AI SDK (no LangChain)
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

# Load prompts
from prompts_config import (
    SQL_GENERATION_PROMPT,
    ANSWER_GENERATION_PROMPT,
    FEW_SHOT_EXAMPLES,
    TABLE_SELECTION_PROMPT,
)

load_dotenv()

DB_TYPE = os.getenv("DB_TYPE", "postgresql").lower()
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "askdb_csv")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
if not GOOGLE_API_KEY:
    raise RuntimeError("GOOGLE_API_KEY is not set")
genai.configure(api_key=GOOGLE_API_KEY)

model = genai.GenerativeModel("gemini-2.0-flash")


def generate_content_with_retry(prompt: str, max_retries: int = 3, initial_delay: float = 1.0):
    """
    Generate content with retry logic and exponential backoff for rate limiting errors.
    
    Args:
        prompt: The prompt to send to the model
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
    
    Returns:
        The response from the model
    
    Raises:
        Exception: If all retries are exhausted
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            res = model.generate_content(prompt)
            return res
        except google_exceptions.ResourceExhausted as e:
            last_exception = e
            if attempt < max_retries:
                # Exponential backoff: 1s, 2s, 4s, etc.
                delay = initial_delay * (2 ** attempt)
                print(f"⚠️ Rate limit hit (429). Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})...")
                time.sleep(delay)
            else:
                print(f"❌ Rate limit error after {max_retries + 1} attempts")
                raise Exception(
                    "API rate limit exceeded. Please wait a moment and try again. "
                    "This usually happens when too many requests are made in a short time period."
                ) from e
        except Exception as e:
            # For other errors, don't retry
            raise
    
    # Should never reach here, but just in case
    if last_exception:
        raise last_exception


def connect_db():
    if DB_TYPE == "sqlite":
        return sqlite3.connect(DB_NAME)
    else:
        import psycopg2
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
        )


def clean_sql_query(text: str) -> str:
    block_pattern = r"```(?:sql|SQL|SQLQuery|mysql|postgresql)?\s*(.*?)\s*```"
    text = re.sub(block_pattern, r"\1", text, flags=re.DOTALL)
    prefix_pattern = r"^(?:SQL\s*Query|SQLQuery|MySQL|PostgreSQL|SQL)\s*:\s*"
    text = re.sub(prefix_pattern, "", text, flags=re.IGNORECASE)
    sql_statement_pattern = r"(SELECT[\s\S]*?;)"
    sql_match = re.search(sql_statement_pattern, text, flags=re.IGNORECASE)
    if sql_match:
        text = sql_match.group(1)
    text = re.sub(r'`([^`]*)`', r'\1', text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_sql(question: str, table_details: str, context: str = "") -> str:
    few_shot = "\n\n".join([
        f"Q: {ex['input']}\nSQLQuery:\n{ex['query']}" for ex in FEW_SHOT_EXAMPLES
    ])
    context_block = (f"\n\nConversation context (recent):\n{context}\n\n" if context else "\n\n")
    prompt = (
        f"{SQL_GENERATION_PROMPT}\n\n"
        f"TABLES:\n{table_details}{context_block}"
        f"Examples:\n{few_shot}\n\n"
        f"User Question: {question}\n"
        f"SQLQuery:"
    )
    res = generate_content_with_retry(prompt)
    text = res.text if hasattr(res, "text") else str(res)
    return clean_sql_query(text)


def execute_sql(sql: str):
    """Execute SQL and return (rows, execution_time_seconds)"""
    import time
    start_time = time.time()
    conn = connect_db()
    try:
        if DB_TYPE == "sqlite":
            cur = conn.cursor()
            cur.execute(sql)
            rows = cur.fetchall()
        else:
            import psycopg2
            with conn.cursor() as cur:
                cur.execute(sql)
                try:
                    rows = cur.fetchall()
                except Exception:
                    rows = [(f"{cur.rowcount} rows affected",)]
        execution_time = time.time() - start_time
        return rows, execution_time
    finally:
        conn.commit()
        conn.close()


def refine_sql(question: str, failed_sql: str, error_message: str, table_details: str) -> str:
    """Use LLM to refine SQL query based on error message"""
    prompt = f"""You are a SQL expert. The following query failed with an error. Analyze the error and provide a CORRECTED query.

Original Question: {question}

Failed SQL Query:
{failed_sql}

Error Message:
{error_message}

Common Issues to Check:
1. Column doesn't exist - verify column names match the schema exactly (case-sensitive, use quotes if needed)
2. Table doesn't exist - check table names are correct (use only tables from: {table_details[:200]})
3. Syntax errors - fix SQL syntax (missing commas, quotes, parentheses)
4. Type mismatches - ensure correct data types (cast TEXT to numeric with NULLIF for ACS tables)
5. JOIN errors - verify JOIN conditions and table aliases
6. Missing quotes - column names with special chars need double quotes: "Geo_STUSAB"

Provide ONLY the corrected SQL query, no explanations:"""
    
    res = generate_content_with_retry(prompt)
    text = res.text if hasattr(res, "text") else str(res)
    return clean_sql_query(text)


def execute_sql_with_retry(sql: str, question: str, table_details: str, max_retries: int = 2):
    """Execute SQL with automatic retry and self-correction"""
    attempts = []
    current_sql = sql
    
    for attempt_num in range(max_retries + 1):
        try:
            rows, execution_time = execute_sql(current_sql)
            return rows, execution_time, current_sql, attempts
        except Exception as e:
            error_msg = str(e)
            attempts.append({
                "attempt": attempt_num + 1,
                "sql": current_sql,
                "error": error_msg
            })
            
            if attempt_num < max_retries:
                print(f"⚠️ Query failed (attempt {attempt_num + 1}/{max_retries + 1}): {error_msg}")
                print(f"🔄 Attempting to correct query...")
                try:
                    current_sql = refine_sql(question, current_sql, error_msg, table_details)
                    print(f"🔧 Corrected SQL: {current_sql[:100]}...")
                except Exception as refine_error:
                    print(f"❌ Error during SQL refinement: {refine_error}")
                    break
            else:
                print(f"❌ All retry attempts exhausted")
                raise
    
    # If we get here, all retries failed
    raise Exception(f"Query failed after {max_retries + 1} attempts. Last error: {error_msg}")


def get_column_suggestions(question: str, table_details: str) -> list:
    """Suggest relevant columns based on question intent using LLM"""
    question_lower = question.lower()
    
    # Check if question is vague (no specific column mentioned)
    has_specific_column = any(
        keyword in question_lower for keyword in 
        ["acs23_5yr", "geo_", "column", "field", "b01001", "b25140"]
    )
    
    if has_specific_column:
        return []  # Don't suggest if user already specified columns
    
    # Use LLM to suggest relevant columns
    prompt = f"""Based on the user's question, suggest 3-5 relevant ACS columns they might want to query.

User Question: {question}

Available Tables:
{table_details[:500]}

Common ACS Column Patterns:
- ACS23_5yr_B01001_* = Population data
- ACS23_5yr_B25140* = Housing data  
- Geo_* = Geographic identifiers (Geo_STUSAB, Geo_STATE, Geo_COUNTY, Geo_qname)

For the user's question, suggest specific column names (with descriptions) that would be most relevant.
Format as: "ColumnName (Description)"

Return only the suggestions, one per line, no numbering:"""
    
    try:
        res = generate_content_with_retry(prompt)
        text = res.text if hasattr(res, "text") else str(res)
        suggestions = [line.strip() for line in text.strip().split('\n') if line.strip()][:5]
        return suggestions if suggestions else []
    except Exception as e:
        print(f"Error generating column suggestions: {e}")
        # Fallback to keyword-based suggestions
        return get_keyword_based_suggestions(question_lower)


def get_keyword_based_suggestions(question_lower: str) -> list:
    """Fallback: keyword-based column suggestions"""
    keywords_to_columns = {
        "population": [
            "ACS23_5yr_B01001_001E (Total Population)",
            "ACS23_5yr_B01001_002E (Male Population)",
            "ACS23_5yr_B01001_026E (Female Population)"
        ],
        "housing": [
            "ACS23_5yr_B25140I001 (Total Housing Units)",
            "ACS23_5yr_B25140I002 (Owner-Occupied)",
            "ACS23_5yr_B25140I003 (Renter-Occupied)"
        ],
        "income": [
            "ACS23_5yr_B19013_001E (Median Household Income)",
            "ACS23_5yr_B19013_001s (Income Standard Error)"
        ],
        "age": [
            "ACS23_5yr_B01001_003E (Male Under 5 years)",
            "ACS23_5yr_B01001_027E (Female Under 5 years)"
        ],
        "state": [
            "Geo_STUSAB (State Code)",
            "Geo_STATE (State FIPS Code)"
        ],
        "county": [
            "Geo_COUNTY (County FIPS Code)",
            "Geo_qname (Geographic Name)"
        ]
    }
    
    for keyword, columns in keywords_to_columns.items():
        if keyword in question_lower:
            return columns[:5]
    
    # Default suggestions
    return [
        "ACS23_5yr_B01001_001E (Total Population)",
        "Geo_STUSAB (State Code)",
        "Geo_COUNTY (County FIPS)",
        "Geo_qname (Geographic Name)"
    ]


def answer_from_result(question: str, result: list) -> str:
    result_str = "No data returned from the database query." if not result else str(result)
    prompt = (
        f"{ANSWER_GENERATION_PROMPT}\n\n"
        f"User Question: {question}\n\n"
        f"Database Query Result: {result_str}"
    )
    res = generate_content_with_retry(prompt)
    return res.text if hasattr(res, "text") else str(res)


# --- Conversation anchoring helpers ---
def extract_primary_table(sql: str) -> str:
    try:
        m = re.search(r"FROM\s+([a-zA-Z_][\w\.]*)(?:\s+AS\s+\w+|\s+\w+)?", sql, flags=re.IGNORECASE)
        if not m:
            return ""
        table = m.group(1)
        return table.split('.')[-1]
    except Exception:
        return ""


def contains_pronoun_followup(q: str) -> bool:
    ql = q.lower()
    return any(p in ql for p in ["them", "those", "it", "that", "these", "name them", "list them"])


def is_definitional_question(q: str) -> bool:
    """Check if the question is asking for a definition/explanation rather than data query"""
    ql = q.lower().strip()
    definition_patterns = [
        "what does", "what is", "what are", "what do", "what's",
        "explain", "define", "meaning", "means", "mean",
        "tell me about", "describe", "definition", "what does that mean"
    ]
    return any(ql.startswith(pattern) or f" {pattern} " in ql for pattern in definition_patterns)


def generate_definition_sql(question: str, context: str = "") -> tuple:
    """
    Generate SQL response for definitional/explanatory questions.
    Returns SQL that will execute and return an explanation.
    
    Returns: (sql, will_execute) tuple
    - sql: SQL query string
    - will_execute: True if SQL should be executed, False if it's just for display
    """
    # Extract what they're asking about from context or question
    # Look for column codes like B01001A011, ACS codes, etc.
    import re
    
    # Try to extract column/table code from question or context
    column_pattern = r'(?:ACS\d+_5yr_)?([A-Z]\d+[A-Z]?\d*)'
    matches = re.findall(column_pattern, question.upper())
    
    if matches:
        code = matches[0]  # e.g., "B01001A011"
        
        # Use LLM to generate explanation
        prompt = f"""Based on the user's question about the ACS code or column "{code}", 
provide a clear explanation of what it represents.

User Question: {question}
Column Code: {code}
Context: {context[:200] if context else "No previous context"}

Common ACS Column Patterns:
- B01001* = Population/Sex by Age data
- B25140* = Housing data
- B19013* = Income data
- Geo_* = Geographic identifiers

For code "{code}", explain what it represents in the ACS dataset.
Provide a concise explanation (1-2 sentences).

Return ONLY the explanation text, no markdown, no code blocks:"""
        
        try:
            res = generate_content_with_retry(prompt)
            explanation = res.text if hasattr(res, "text") else str(res)
            explanation = explanation.strip().strip('"').strip("'")
            
            # Generate SQL in the format: SELECT 'explanation' AS meaning;
            # Escape single quotes in explanation (SQL escaping: ' becomes '')
            escaped_explanation = explanation.replace("'", "''")
            sql = f"SELECT '{escaped_explanation}' AS meaning;"
            return sql, True  # Execute this SQL to return the explanation
        except Exception as e:
            print(f"Error generating definition: {e}")
            return None, False
    
    # If no specific code found, generate generic explanation SQL
    prompt = f"""The user is asking for an explanation or definition, not a database query.

User Question: {question}
Context: {context[:200] if context else "No previous context"}

Provide a helpful explanation or answer to their question.
Return ONLY the explanation text:"""
    
    try:
        res = generate_content_with_retry(prompt)
        explanation = res.text if hasattr(res, "text") else str(res)
        explanation = explanation.strip().strip('"').strip("'")
        
        # Generate SQL in the format: SELECT 'explanation' AS meaning;
        # Escape single quotes in explanation (SQL escaping: ' becomes '')
        escaped_explanation = explanation.replace("'", "''")
        sql = f"SELECT '{escaped_explanation}' AS meaning;"
        return sql, True
    except Exception as e:
        print(f"Error generating definition: {e}")
        return None, False

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

# Enable logging
import logging
logging.basicConfig(level=logging.DEBUG)
app.logger.setLevel(logging.DEBUG)

# Server start timestamp - used to clear old sessions on restart
SERVER_START_TIME = str(time.time())


@app.route("/")
def index():
    return render_template("native_index.html")


@app.route("/api/session/clear", methods=["POST"])
def clear_session():
    """Clear the current session (conversation history) on server"""
    try:
        session.clear()
        session['server_start_time'] = SERVER_START_TIME  # Reset session timestamp
        return jsonify({
            "success": True,
            "message": "Session cleared successfully"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route("/api/session/status", methods=["GET"])
def get_session_status():
    """Get current session status"""
    try:
        history = session.get('history', [])
        return jsonify({
            "active": True,
            "history_length": len(history),
            "has_history": len(history) > 0
        })
    except Exception as e:
        return jsonify({
            "active": False,
            "error": str(e)
        }), 500


@app.route("/api", methods=["POST"])
def api():
    try:
        # Clear session if it's from before server restart
        if session.get('server_start_time') != SERVER_START_TIME:
            session.clear()
            session['server_start_time'] = SERVER_START_TIME
        
        data = request.get_json(force=True)
        question = data.get("question", "").strip()
        if not question:
            return jsonify({"error": "No question provided"}), 400

        # Minimal table details (reuse CSV like existing app)
        table_details = ""
        try:
            import pandas as pd
            # Read CSV without header, specify column names
            df = pd.read_csv("database_table_descriptions.csv", header=None, names=['table_name', 'description'])
            for _, row in df.iterrows():
                table_details += f"Table Name: {row['table_name']}\nTable Description: {row['description']}\n\n"
        except Exception as e:
            print(f"Error reading database_table_descriptions.csv: {e}")
            table_details = "acs_demographics, acs_housing, states, counties, metro_areas"

        # Build short conversation context from previous turns
        history = session.get('history', [])
        ctx_lines = []
        for turn in history[-4:]:
            ctx_lines.append(f"Previous Q: {turn.get('q','')}")
            if turn.get('sql'):
                ctx_lines.append(f"Previous SQL: {turn.get('sql')}")
                # Extract what was queried from SQL for better pronoun resolution
                sql_lower = turn.get('sql', '').lower()
                if 'count(distinct' in sql_lower:
                    # Extract column name from COUNT(DISTINCT column)
                    match = re.search(r'count\s*\(\s*distinct\s+["\']?(\w+)["\']?', sql_lower)
                    if match:
                        col = match.group(1)
                        ctx_lines.append(f"Previous query was counting distinct values of: {col}")
                elif 'select distinct' in sql_lower:
                    match = re.search(r'select\s+distinct\s+["\']?(\w+)["\']?', sql_lower)
                    if match:
                        col = match.group(1)
                        ctx_lines.append(f"Previous query selected distinct values of: {col}")
            if turn.get('rows_summary'):
                ctx_lines.append(f"Previous Results: {turn.get('rows_summary')}")
            ctx_lines.append(f"Previous A: {turn.get('a','')}")
        ctx_text = "\n".join(ctx_lines)

        # Anchor to previous primary table if pronoun-style follow-up
        last_sql_ctx = session.get('last_sql', '')
        last_primary = extract_primary_table(last_sql_ctx) if last_sql_ctx else ""
        
        # Always include last table context for better anchoring
        if last_primary and history:
            ctx_text = (ctx_text + f"\n\nPrevious query used table: {last_primary}. For follow-up questions, continue using this table unless explicitly asked to switch.").strip()
        
        # Extra emphasis for pronoun follow-ups
        if contains_pronoun_followup(question) and last_sql_ctx:
            if last_primary:
                ctx_text = (ctx_text + f"\nIMPORTANT: The user's question uses pronouns ('them', 'those', 'it', etc.) referring to the previous query results. Use the same table ({last_primary}) and reference the previous SQL query structure.").strip()

        # Generate, execute, answer
        last_sql = ""
        sql = generate_sql(question, table_details, context=ctx_text)
        last_sql = sql
        
        # Validate SQL uses existing tables from database_table_descriptions.csv
        try:
            import pandas as pd
            # Read CSV without header, specify column names
            df = pd.read_csv("database_table_descriptions.csv", header=None, names=['table_name', 'description'])
            valid_tables = set(df['table_name'].str.lower())
            
            # Extract table names from SQL (handle quoted and unquoted, with/without aliases)
            sql_lower = sql.lower()
            # Match: FROM table, FROM "table", FROM table AS alias, FROM "table" AS alias
            # Improved pattern: handles quoted identifiers (PostgreSQL style) and unquoted
            from_pattern = r'from\s+(?:"([^"]+)"|([a-zA-Z_][\w\.]*))(?:\s+as\s+\w+)?'
            join_pattern = r'join\s+(?:"([^"]+)"|([a-zA-Z_][\w\.]*))(?:\s+as\s+\w+)?'
            from_matches = re.findall(from_pattern, sql_lower)
            join_matches = re.findall(join_pattern, sql_lower)
            # Extract table names (group 0 is quoted, group 1 is unquoted)
            from_sql = [m[0] if m[0] else m[1] for m in from_matches if m[0] or m[1]]
            join_sql = [m[0] if m[0] else m[1] for m in join_matches if m[0] or m[1]]
            # Handle schema.table format and strip quotes
            all_tables_in_sql = set([t.split('.')[-1].strip('"\'') for t in from_sql + join_sql if t])
            
            # Check if any table in SQL doesn't exist in our valid tables
            invalid_tables = [t for t in all_tables_in_sql if t and t not in valid_tables]
            if invalid_tables:
                print(f"⚠️ Invalid table names detected: {invalid_tables}")
                print(f"   Valid tables: {valid_tables}")
                print(f"   Tables in SQL: {all_tables_in_sql}")
                # Regenerate SQL with stronger instruction
                valid_table_list = ', '.join([f"'{t}'" for t in df['table_name'].tolist()])
                error_msg = f"CRITICAL ERROR: Invalid table names detected in SQL: {invalid_tables}. The database only contains these tables: {valid_table_list}. You MUST use only these table names."
                table_details_with_error = f"{table_details}\n\n{error_msg}\n\nRegenerate the SQL query using ONLY the valid table names listed above."
                sql = generate_sql(question, table_details_with_error, context=ctx_text)
                last_sql = sql
                # Validate again after regeneration
                sql_lower2 = sql.lower()
                from_matches2 = re.findall(from_pattern, sql_lower2)
                join_matches2 = re.findall(join_pattern, sql_lower2)
                from_sql2 = [m[0] if m[0] else m[1] for m in from_matches2 if m[0] or m[1]]
                join_sql2 = [m[0] if m[0] else m[1] for m in join_matches2 if m[0] or m[1]]
                all_tables_in_sql2 = set([t.split('.')[-1].strip('"\'') for t in from_sql2 + join_sql2 if t])
                invalid_tables2 = [t for t in all_tables_in_sql2 if t and t not in valid_tables]
                if invalid_tables2:
                    # If still invalid, try one more time with even stronger message
                    error_msg2 = f"STOP! You are using invalid table names: {invalid_tables2}. The ONLY valid tables are: {valid_table_list}. Replace ALL table names in your SQL with these valid names."
                    sql = generate_sql(question, f"{table_details}\n\n{error_msg2}", context="")
                    last_sql = sql
        except Exception as e:
            print(f"Table validation error: {e}")  # Debug: log the error
            pass  # If validation fails, proceed with original SQL
        
        # Execute SQL with retry and self-correction
        try:
            rows, execution_time, final_sql, retry_attempts = execute_sql_with_retry(sql, question, table_details, max_retries=2)
            sql = final_sql  # Use the corrected SQL if it was refined
        except Exception as e:
            # If retry also failed, raise the error (will be caught by outer exception handler)
            raise
        
        answer = answer_from_result(question, rows)
        
        # Create a summary of results for context
        rows_summary = ""
        if rows:
            if len(rows) == 1:
                rows_summary = f"Single result: {rows[0]}"
            elif len(rows) <= 5:
                rows_summary = f"{len(rows)} results: {rows}"
            else:
                rows_summary = f"{len(rows)} results. First few: {rows[:3]}"
        else:
            rows_summary = "No results returned"
        
        # Update history (keep last 10 turns) and last_sql
        history.append({
            "q": question, 
            "a": answer, 
            "sql": sql,
            "rows_summary": rows_summary
        })
        session['history'] = history[-10:]
        session['last_sql'] = sql

        # Pagination: limit rows returned, include total count
        rows_limit = 50  # Show first 50 rows
        total_rows = len(rows)
        rows_to_return = rows[:rows_limit]
        
        # Get column suggestions if query seems vague or user might benefit
        column_suggestions = []
        try:
            # Only suggest if question doesn't mention specific columns
            question_lower = question.lower()
            if not any(keyword in question_lower for keyword in ["acs23_5yr", "geo_", "column", "field", "b01001", "b25140"]):
                column_suggestions = get_column_suggestions(question, table_details)
        except Exception as e:
            print(f"Error getting column suggestions: {e}")
        
        # Get query suggestions based on current question and results
        query_suggestions = []
        try:
            from query_suggestions import generate_query_suggestions
            rows_summary = f"{total_rows} result{'s' if total_rows != 1 else ''}" if total_rows > 0 else "No results"
            query_suggestions = generate_query_suggestions(
                question=question,
                sql=sql,
                answer=answer,
                rows_summary=rows_summary,
                table_details=table_details
            )
        except Exception as e:
            print(f"Error getting query suggestions: {e}")
        
        return jsonify({
            "sql": sql, 
            "rows": rows_to_return, 
            "answer": answer,
            "execution_time": round(execution_time, 3),
            "total_rows": total_rows,
            "rows_shown": len(rows_to_return),
            "has_more": total_rows > rows_limit,
            "column_suggestions": column_suggestions,
            "query_suggestions": query_suggestions
        })
    except Exception as e:
        # Log the full error for debugging
        import traceback
        error_trace = traceback.format_exc()
        print(f"ERROR in /api endpoint: {str(e)}")
        print(f"Traceback: {error_trace}")
        
        # Convert technical errors to plain English
        error_msg = str(e)
        plain_error = convert_error_to_plain_english(error_msg)
        
        # Include last attempted SQL so UI can always show it
        try:
            return jsonify({
                "error": plain_error,
                "error_technical": error_msg if app.debug else None,
                "sql": last_sql if 'last_sql' in locals() else "",
                "traceback": error_trace if app.debug else None
            }), 500
        except Exception as e2:
            return jsonify({
                "error": "An unexpected error occurred. Please try again.",
                "error_technical": f"Error handling error: {str(e2)}. Original error: {str(e)}",
                "sql": ""
            }), 500


def convert_error_to_plain_english(error_msg: str) -> str:
    """Convert technical database errors to user-friendly messages"""
    error_lower = error_msg.lower()
    
    # Table doesn't exist
    if "does not exist" in error_lower or "relation" in error_lower:
        if "table" in error_lower or "relation" in error_lower:
            return "The table you're trying to query doesn't exist in the database. Please check the table name and try again."
    
    # Column doesn't exist
    if "column" in error_lower and "does not exist" in error_lower:
        return "One of the columns in your query doesn't exist. The database schema may have changed. Please rephrase your question."
    
    # Syntax errors
    if "syntax error" in error_lower:
        return "There's a syntax error in the generated SQL query. Please try rephrasing your question."
    
    # Connection errors
    if "connection" in error_lower or "could not connect" in error_lower:
        return "Unable to connect to the database. Please check if the database server is running."
    
    # Permission errors
    if "permission" in error_lower or "access denied" in error_lower:
        return "You don't have permission to perform this operation. Please contact your administrator."
    
    # Timeout errors
    if "timeout" in error_lower or "timed out" in error_lower:
        return "The query took too long to execute. Try making your question more specific or add filters to reduce the amount of data."
    
    # Rate limit errors (429)
    if "rate limit" in error_lower or "resource exhausted" in error_lower or "429" in error_msg:
        return "The API rate limit has been exceeded. Please wait a moment and try again. This usually happens when too many requests are made in a short time period."
    
    # Generic fallback
    return f"An error occurred while processing your query: {error_msg}. Please try rephrasing your question or contact support if the problem persists."


if __name__ == "__main__":
    port = int(os.getenv("PORT", "2003"))
    app.run(debug=True, port=port)


