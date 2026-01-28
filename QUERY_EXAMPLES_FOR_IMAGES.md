# Query Examples for Report Images

This document contains suggested queries that will make excellent screenshots for the AskDB project report. Each query demonstrates specific features and capabilities of the system.

## 🎯 Screenshot Recommendations

### Screenshot 1: Basic Query - Simple Count
**Purpose**: Demonstrate core functionality and clean interface

**Query**: 
```
How many records are in the acs_demographics table?
```

**Expected Result**: 
- SQL: `SELECT COUNT(*) FROM acs_demographics;`
- Answer: "There are X records in the acs_demographics table."

**What to Capture**:
- Clean interface with question input
- Generated SQL query displayed
- Natural language answer
- Execution time shown

---

### Screenshot 2: Aggregation Query - Population Sum
**Purpose**: Show aggregation with geographic filtering

**Query**:
```
Show me the total population for California
```

**Expected SQL**:
```sql
SELECT SUM(NULLIF(NULLIF("ACS23_5yr_B01001_001E", ''), '.')::numeric) 
AS total_population
FROM acs_demographics
WHERE "Geo_STUSAB" = 'CA';
```

**What to Capture**:
- SQL with proper casting (demonstrates ACS data handling)
- Result with formatted number
- Execution time

---

### Screenshot 3: Complex Query - Top Results with JOIN
**Purpose**: Demonstrate JOINs, aggregations, and ordering

**Query**:
```
What are the top 5 states by total population? Show state names.
```

**Expected SQL**:
```sql
SELECT s.state_name, 
       SUM(NULLIF(NULLIF(ad."ACS23_5yr_B01001_001E", ''), '.')::numeric) 
       AS total_pop
FROM acs_demographics AS ad
JOIN states AS s ON ad."Geo_STUSAB" = s.state_code
GROUP BY s.state_name
ORDER BY total_pop DESC
LIMIT 5;
```

**What to Capture**:
- Complex SQL query with JOIN
- Results table with state names and populations
- Clean formatting of results

---

### Screenshot 4: Multi-Table JOIN - Counties
**Purpose**: Show complex JOINs with multiple conditions

**Query**:
```
Show me county names and population for Georgia counties, ordered by population
```

**Expected SQL**:
```sql
SELECT c.county_name,
       ad."ACS23_5yr_B01001_001E" AS population
FROM acs_demographics AS ad
JOIN counties AS c 
  ON ad."Geo_STATE" = c.state_fips 
  AND ad."Geo_COUNTY" = c.county_fips
WHERE ad."Geo_STUSAB" = 'GA'
ORDER BY 
  NULLIF(NULLIF(ad."ACS23_5yr_B01001_001E", ''), '.')::numeric DESC;
```

**What to Capture**:
- Multi-condition JOIN
- Results table with county names
- Proper ordering displayed

---

### Screenshot 5: Text Search Query
**Purpose**: Demonstrate text search capabilities

**Query**:
```
Find all places containing 'San Francisco' in the housing data
```

**Expected SQL**:
```sql
SELECT "Geo_qname", "Geo_GEO_ID"
FROM acs_housing
WHERE "Geo_qname" ILIKE '%San Francisco%'
LIMIT 20;
```

**What to Capture**:
- SQL with ILIKE pattern matching
- Results showing matching geographic areas
- Multiple results displayed

---

### Screenshot 6: Context-Aware Conversation (PART 1)
**Purpose**: Show conversation context handling

**First Query**:
```
Show me all distinct states in the database
```

**Expected Result**: List of all states

**Capture**: First query and result

---

### Screenshot 7: Context-Aware Conversation (PART 2)
**Purpose**: Demonstrate pronoun resolution and follow-up

**Second Query** (after Screenshot 6):
```
What are the top 3 by population?
```

**Expected Behavior**:
- System understands "top 3" refers to states from previous query
- SQL includes state filtering/grouping
- Shows top 3 states by population

**What to Capture**:
- Conversation history showing both queries
- How the system interpreted the follow-up
- Both SQL queries visible
- Results showing top 3 states

---

### Screenshot 8: Error Handling and Auto-Correction
**Purpose**: Demonstrate self-correction mechanism

**Query** (intentionally using wrong table):
```
Show me all customers in the database
```

**Expected Flow**:
1. **First Attempt**: 
   - SQL: `SELECT * FROM customers;`
   - Error: "relation 'customers' does not exist"

2. **Auto-Correction**:
   - System detects error
   - Regenerates SQL: `SELECT * FROM contacts;` (or appropriate table)
   - Success

**What to Capture** (if possible):
- Error message displayed
- Then correction happening
- Final successful result

**Alternative** (if error is auto-corrected instantly):
- Capture the final successful result
- Note in caption that error was auto-corrected

---

### Screenshot 9: Query Suggestions Feature
**Purpose**: Show proactive query suggestions

**Initial Query**:
```
Show me population data for California
```

**After Result Displayed**:
- System shows query suggestions like:
  - "Show me the breakdown by county"
  - "What about housing data for California?"
  - "Compare with another state"
  - "Show me income data for California"

**What to Capture**:
- Results from initial query
- Query suggestions box displayed below
- Multiple suggestions visible
- Suggestions are clickable (show hover state)

---

### Screenshot 10: Column Suggestions Feature
**Purpose**: Demonstrate column suggestions for vague queries

**Query** (vague, no specific columns):
```
What population data do we have available?
```

**Expected Result**:
- System detects vague question
- Shows column suggestions box with:
  - `ACS23_5yr_B01001_001E (Total Population)`
  - `ACS23_5yr_B01001_002E (Male Population)`
  - `ACS23_5yr_B01001_026E (Female Population)`
  - etc.

**What to Capture**:
- Query input
- Column suggestions box highlighted
- Multiple column suggestions with descriptions
- Suggestions are clickable

---

### Screenshot 11: Definitional Question
**Purpose**: Show handling of definition/explanation questions

**Query**:
```
What does ACS23_5yr_B01001_001E mean?
```

**Expected Result**:
- System detects definitional question
- Returns explanation without querying database
- Explanation: "ACS23_5yr_B01001_001E represents the Total Population estimate from the American Community Survey 2023 5-year data..."

**What to Capture**:
- Query input
- Explanation displayed (not a database result)
- Natural language explanation visible

---

### Screenshot 12: Multi-Step Analysis Workflow
**Purpose**: Demonstrate progressive data exploration

**Sequence of Queries**:

1. **Q1**: "What's the total population in California?"
   - Result: Shows total number

2. **Q2**: "Break that down by county"
   - Result: Shows list of counties with populations

3. **Q3**: "Show me the top 5 counties"
   - Result: Shows top 5 counties by population

**What to Capture**:
- Full conversation history
- All three queries visible
- Each with its SQL and result
- Demonstrates natural conversation flow

---

### Screenshot 13: Result Pagination
**Purpose**: Show handling of large result sets

**Query**:
```
Show me all counties in California with their populations
```

**Expected Result**:
- Large result set (potentially hundreds of rows)
- Message: "Showing 50 of 234 results"
- Execution time displayed
- Total count shown

**What to Capture**:
- Results table (first 50 rows visible)
- Pagination message at bottom
- "has_more" indicator visible
- Execution statistics

---

### Screenshot 14: Housing Data Query
**Purpose**: Demonstrate different data domain

**Query**:
```
What's the total number of housing units in New York?
```

**Expected SQL**:
```sql
SELECT SUM(NULLIF(NULLIF("ACS23_5yr_B25140I001", ''), '.')::numeric) 
AS total_housing
FROM acs_housing
WHERE "Geo_STUSAB" = 'NY';
```

**What to Capture**:
- Query using housing table
- Results showing housing metrics
- Different from population queries (shows versatility)

---

### Screenshot 15: Comparison Query
**Purpose**: Show comparative analysis

**Query**:
```
Compare the total population of California and Texas
```

**Expected SQL**:
```sql
SELECT "Geo_STUSAB", 
       SUM(NULLIF(NULLIF("ACS23_5yr_B01001_001E", ''), '.')::numeric) 
       AS total_pop
FROM acs_demographics
WHERE "Geo_STUSAB" IN ('CA', 'TX')
GROUP BY "Geo_STUSAB"
ORDER BY "Geo_STUSAB";
```

**What to Capture**:
- SQL with IN clause for comparison
- Results showing both states side by side
- Formatted comparison display

---

## 📸 Image Caption Suggestions

For each screenshot in your report, use these caption formats:

### Basic Query
**Caption**: "Basic query example demonstrating AskDB's natural language to SQL conversion. User asks 'How many records are in the acs_demographics table?' and receives a syntactically correct SQL query with natural language response."

### Complex Query with JOIN
**Caption**: "Complex query involving table JOINs and aggregations. The system automatically generates SQL to find top 5 states by population, joining the demographics table with the states reference table for human-readable names."

### Context-Aware Conversation
**Caption**: "Context-aware conversation handling. The system maintains conversation history, allowing follow-up questions like 'What are the top 3?' to reference previous query results without requiring the user to re-specify context."

### Self-Correction
**Caption**: "Automatic error correction mechanism. When the initial query fails due to an incorrect table name, AskDB automatically analyzes the error and regenerates a corrected query, successfully returning results without user intervention."

### Query Suggestions
**Caption**: "Proactive query suggestions system. After displaying query results, AskDB suggests relevant follow-up questions to help users explore the data more effectively, demonstrating intelligent assistance capabilities."

---

## 🎨 Screenshot Quality Tips

1. **Use High Resolution**: Capture at 1920x1080 or higher
2. **Show Full Context**: Include enough of the UI to show features
3. **Highlight Key Elements**: Use annotations/arrows for important features
4. **Consistent Styling**: Use same browser window size for all screenshots
5. **Remove Sensitive Data**: Ensure no personal/confidential data visible
6. **Clear Text**: Ensure SQL and results are readable
7. **Show Loading States**: If possible, capture loading indicators
8. **Multiple Views**: For complex features, use multiple angles

---

## 📊 Recommended Image Sequence for Report

1. **Cover/Title**: Screenshot of welcome screen
2. **Introduction**: Screenshot 1 (Basic Query)
3. **Architecture**: System diagram (create separately)
4. **Features - Basic**: Screenshot 2 (Aggregation)
5. **Features - Complex**: Screenshot 3 (JOINs)
6. **Features - Context**: Screenshot 7 (Conversation)
7. **Features - Error Handling**: Screenshot 8 (Auto-correction)
8. **Features - Suggestions**: Screenshot 9 (Query suggestions)
9. **Features - Column Help**: Screenshot 10 (Column suggestions)
10. **Use Cases**: Screenshot 12 (Multi-step workflow)
11. **Results Section**: Screenshot 15 (Comparison query)

---

## 💡 Additional Tips

- **Test Queries First**: Run each query to ensure it works before screenshot
- **Use Real Data**: Ensure results look realistic and meaningful
- **Add Annotations**: Use arrows/circles to highlight key features
- **Consistent Theme**: Use same browser theme/style for all screenshots
- **Include Metadata**: Note query execution time in screenshots if visible
- **Show Interactions**: If possible, show hover states or clicked elements

---

## 🚀 Quick Test Commands

Before taking screenshots, test these queries work:

```bash
# Basic count
curl -X POST http://localhost:2003/api \
  -H "Content-Type: application/json" \
  -d '{"question": "How many records are in acs_demographics?"}'

# Population query
curl -X POST http://localhost:2003/api \
  -H "Content-Type: application/json" \
  -d '{"question": "Show me the total population for California"}'

# Top states
curl -X POST http://localhost:2003/api \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the top 5 states by total population? Show state names."}'
```

Good luck with your report! 📄✨


