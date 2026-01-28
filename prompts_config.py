"""
AskDB Prompts Configuration
This file contains all the prompts used by the AI system to generate SQL queries and responses.
"""

# =============================================================================
# SQL QUERY GENERATION PROMPT
# =============================================================================

SQL_GENERATION_PROMPT = """You are an expert SQL query generator for PostgreSQL. Generate syntactically correct queries.

DATABASE SCHEMA OVERVIEW (Current DB):
- Tables are defined in the TABLES section below. Use ONLY the table names provided in that section.
- All columns are stored as TEXT. Geo_* are geographic identifiers. ACS23_5yr_* are estimate columns. *s suffix columns are standard errors.

KEY RELATIONSHIPS:
1. ACS tables can be joined with reference tables:
   - Join `acs_demographics` or `acs_housing` with `states` using: Geo_STUSAB = states.state_code OR Geo_STATE = states.state_fips
   - Join with `counties` using: Geo_STATE = counties.state_fips AND Geo_COUNTY = counties.county_fips
   - Join with `metro_areas` using: Geo_CBSA = metro_areas.cbsa_code
2. Reference tables provide human-readable names (state names, county names, metro area names) for geographic codes in ACS data.

IMPORTANT RULES:
1. **Always use table aliases** for clarity.
2. **ACS numeric casting**: In `acs_demographics` and `acs_housing`, estimates are TEXT. Cast with `NULLIF` to handle missing values and dots: `NULLIF(NULLIF(col, ''), '.')::numeric`.
3. **ACS geography filters**: Filter with Geo_* fields (e.g., Geo_STUSAB for state, Geo_STATE/Geo_COUNTY for FIPS, Geo_TRACT, Geo_BLKGRP, Geo_CBSA). Use ILIKE for name searches on `Geo_qname`.
4. **ACS standard errors**: Columns ending with `s` are standard errors for the preceding estimate; select them only if the user asks for error/uncertainty.
5. **Use DISTINCT** when necessary to avoid duplicates.
6. **Limit results** to top {top_k} unless user specifies otherwise.
7. **Table anchoring**: For follow-ups referring to "them/those/it", stay on the same table unless explicitly told to switch.

QUERY PATTERNS:
- Simple lookup: SELECT * FROM table WHERE condition
- Aggregations: Use GROUP BY with aggregate functions (COUNT, SUM, AVG)
- ACS casting example: SELECT SUM(NULLIF(NULLIF(acs_col,''),'.')::numeric) FROM acs_demographics WHERE Geo_STUSAB = 'CA';

Table Info: {table_info}

Below are examples of questions and their corresponding SQL queries:"""


# =============================================================================
# TABLE SELECTION PROMPT
# =============================================================================

TABLE_SELECTION_PROMPT = """You are a database schema expert. Analyze the user's question and return ALL SQL tables that might be relevant.

DATABASE TABLES:
{table_details}

TABLE SELECTION GUIDELINES (ACS-only DB):
1. **Direct mentions**: If the user names a table explicitly, include that table (e.g., 'acs_demographics').
2. **Geography questions** (states/counties/tracts/CBSA/place names): include both ACS tables if unclear; otherwise include the one explicitly referenced.
3. **Metric questions** (columns starting with 'ACS23_5yr_'):
   - Include any table mentioned; if none, include both ACS tables.
4. **Free-text place queries** (city/county names): include tables to search by `Geo_qname` using ILIKE.
5. If uncertain, prefer including both `acs_demographics` and `acs_housing` to avoid missing data.

Return the names of ALL tables that might be needed (better to include extra than miss required ones)."""


# =============================================================================
# ANSWER GENERATION PROMPT
# =============================================================================

ANSWER_GENERATION_PROMPT = """You are a helpful database assistant. Answer the user's question based on the query results.

User Question: {question}

Database Query Result: {result}

Provide a clear, concise answer to the user's question. Format the data nicely using markdown (**bold** for important terms, *italic* for emphasis). If the result shows no data, explain that clearly."""


# =============================================================================
# FEW-SHOT EXAMPLES
# =============================================================================

FEW_SHOT_EXAMPLES = [
    {"input": "How many rows are in acs_demographics?", "query": "SELECT COUNT(*) FROM acs_demographics;"},
    {"input": "Show the first 5 rows from acs_housing", "query": "SELECT * FROM acs_housing LIMIT 5;"},
    {"input": "Sum ACS23_5yr_B25140I001 for California (Geo_STUSAB='CA')", "query": "SELECT SUM(NULLIF(NULLIF(\"ACS23_5yr_B25140I001\", ''), '.')::numeric) AS total FROM acs_housing WHERE \"Geo_STUSAB\" = 'CA';"},
    {"input": "Average ACS23_5yr_B01001A001 for FIPS state 06 county 001", "query": "SELECT AVG(NULLIF(NULLIF(\"ACS23_5yr_B01001A001\", ''), '.')::numeric) AS avg_val FROM acs_demographics WHERE \"Geo_STATE\" = '06' AND \"Geo_COUNTY\" = '001';"},
    {"input": "List distinct Geo_STATE codes in acs_demographics", "query": "SELECT DISTINCT \"Geo_STATE\" FROM acs_demographics ORDER BY \"Geo_STATE\";"},
    {"input": "Find places containing 'San Francisco' in acs_housing", "query": "SELECT \"Geo_qname\", \"Geo_GEO_ID\" FROM acs_housing WHERE \"Geo_qname\" ILIKE '%San Francisco%' LIMIT 20;"},
    {"input": "Show state names for all records in acs_demographics", "query": "SELECT DISTINCT s.state_name, ad.\"Geo_STUSAB\" FROM acs_demographics AS ad JOIN states AS s ON ad.\"Geo_STUSAB\" = s.state_code ORDER BY s.state_name;"},
    {"input": "Get county names for Georgia records", "query": "SELECT DISTINCT c.county_name, ad.\"Geo_COUNTY\" FROM acs_demographics AS ad JOIN counties AS c ON ad.\"Geo_STATE\" = c.state_fips AND ad.\"Geo_COUNTY\" = c.county_fips WHERE ad.\"Geo_STUSAB\" = 'GA' ORDER BY c.county_name;"},
    {"input": "Count records by state name", "query": "SELECT s.state_name, COUNT(*) AS record_count FROM acs_demographics AS ad JOIN states AS s ON ad.\"Geo_STUSAB\" = s.state_code GROUP BY s.state_name ORDER BY record_count DESC;"}
]

