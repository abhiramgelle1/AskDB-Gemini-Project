"""
Query Suggestions Module
Generates related query suggestions based on current question and results
"""
import os
import time
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv

load_dotenv()

# Initialize Google Generative AI model
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
                print(f"⚠️ Rate limit hit (429) in query suggestions. Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries + 1})...")
                time.sleep(delay)
            else:
                print(f"❌ Rate limit error after {max_retries + 1} attempts in query suggestions")
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


def generate_query_suggestions(question: str, sql: str, answer: str, rows_summary: str = "", table_details: str = "") -> list:
    """
    Generate related query suggestions based on current question, SQL, and results.
    
    Args:
        question: The original user question
        sql: The SQL query that was executed
        answer: The answer/response given to the user
        rows_summary: Summary of the results (e.g., "5 results", "No results")
        table_details: Available table information
    
    Returns:
        List of suggested questions (strings)
    """
    try:
        prompt = f"""Based on the user's question and the query results, suggest 3-5 related questions they might want to ask next.

User's Question: {question}

SQL Query Used: {sql}

Answer/Result: {answer}

Results Summary: {rows_summary}

Available Tables:
{table_details[:500] if table_details else "ACS demographics and housing tables"}

Guidelines for suggestions:
1. Suggest questions that explore related aspects of the data
2. If the query returned results, suggest drilling down or filtering further
3. If the query returned no results, suggest alternative approaches
4. Suggest aggregations, comparisons, or different perspectives
5. Keep suggestions concise and actionable
6. Make suggestions specific to the data domain (ACS demographics/housing)

Return only the suggested questions, one per line, no numbering or bullets.
Format: Just the question text, one per line."""

        response = generate_content_with_retry(prompt)
        text = response.text if hasattr(response, "text") else str(response)
        
        # Parse suggestions (one per line)
        suggestions = [line.strip() for line in text.strip().split('\n') if line.strip()]
        
        # Filter out any lines that don't look like questions
        suggestions = [s for s in suggestions if s.endswith('?') or any(word in s.lower() for word in ['what', 'how', 'show', 'list', 'find', 'get', 'which', 'where', 'when', 'who'])]
        
        # Limit to 5 suggestions
        return suggestions[:5]
        
    except Exception as e:
        print(f"Error generating query suggestions: {e}")
        # Fallback to keyword-based suggestions
        return get_keyword_based_suggestions(question, sql, answer)


def get_keyword_based_suggestions(question: str, sql: str, answer: str) -> list:
    """
    Fallback: Generate suggestions based on keywords and patterns.
    """
    question_lower = question.lower()
    sql_lower = sql.lower()
    suggestions = []
    
    # Pattern 1: If query is about counts, suggest details
    if 'count' in sql_lower or 'how many' in question_lower:
        if 'state' in question_lower or 'geo_stusab' in sql_lower:
            suggestions.append("Show me the breakdown by county")
            suggestions.append("What are the top 5 states by this metric?")
        if 'county' in question_lower or 'geo_county' in sql_lower:
            suggestions.append("Show me the breakdown by state")
            suggestions.append("What are the top 10 counties?")
        suggestions.append("Show me more details about these results")
    
    # Pattern 2: If query filters by state, suggest other states
    if "geo_stusab" in sql_lower or "state" in question_lower:
        suggestions.append("Compare this with another state")
        suggestions.append("Show me the national average")
        suggestions.append("What are the top 5 states?")
    
    # Pattern 3: If query is about demographics, suggest housing
    if 'acs_demographics' in sql_lower or 'population' in question_lower:
        suggestions.append("What about housing data for this area?")
        suggestions.append("Show me income data")
    
    # Pattern 4: If query is about housing, suggest demographics
    if 'acs_housing' in sql_lower or 'housing' in question_lower:
        suggestions.append("What about population data for this area?")
        suggestions.append("Show me demographic breakdowns")
    
    # Pattern 5: If no results, suggest alternatives
    if 'no results' in answer.lower() or 'no data' in answer.lower():
        suggestions.append("Try a different state or county")
        suggestions.append("Search by geographic name instead")
        suggestions.append("Check if the data exists in other tables")
    
    # Pattern 6: If results exist, suggest aggregations
    if 'no results' not in answer.lower() and 'no data' not in answer.lower():
        if 'group by' not in sql_lower:
            suggestions.append("Show me the breakdown by state")
            suggestions.append("Group these results by county")
        if 'order by' not in sql_lower:
            suggestions.append("Show me the top 10 results")
            suggestions.append("Sort by the highest values")
    
    # Default suggestions if nothing matches
    if not suggestions:
        suggestions = [
            "Show me more details",
            "What are the top 10 results?",
            "Break this down by state",
            "Compare with other areas"
        ]
    
    return suggestions[:5]


def analyze_query_intent(question: str, sql: str) -> dict:
    """
    Analyze the intent of the query to generate better suggestions.
    
    Returns:
        Dictionary with intent analysis (type, filters, aggregations, etc.)
    """
    sql_lower = sql.lower()
    question_lower = question.lower()
    
    intent = {
        "type": "unknown",
        "has_filters": False,
        "has_aggregations": False,
        "has_joins": False,
        "tables": [],
        "columns": []
    }
    
    # Detect query type
    if 'count(' in sql_lower or 'how many' in question_lower:
        intent["type"] = "count"
        intent["has_aggregations"] = True
    elif 'sum(' in sql_lower or 'total' in question_lower:
        intent["type"] = "sum"
        intent["has_aggregations"] = True
    elif 'avg(' in sql_lower or 'average' in question_lower:
        intent["type"] = "average"
        intent["has_aggregations"] = True
    elif 'select *' in sql_lower or 'show' in question_lower or 'list' in question_lower:
        intent["type"] = "list"
    
    # Detect filters
    if 'where' in sql_lower:
        intent["has_filters"] = True
    
    # Detect joins
    if 'join' in sql_lower:
        intent["has_joins"] = True
    
    # Extract tables
    import re
    from_matches = re.findall(r'from\s+["\']?(\w+)["\']?', sql_lower)
    join_matches = re.findall(r'join\s+["\']?(\w+)["\']?', sql_lower)
    intent["tables"] = list(set(from_matches + join_matches))
    
    return intent




