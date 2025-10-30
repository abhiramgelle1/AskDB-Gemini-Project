# 📝 AskDB Prompts Configuration Guide

This document explains how the prompts system works and how to maintain it.

## File Structure

```
AskDB/
├── prompts_config.py           # All AI prompts and examples
├── database_table_descriptions.csv  # Table schema information
├── untitled0.py                # Main AI engine (uses prompts)
└── PROMPTS_README.md          # This file
```

## Configuration Files

### 1. `prompts_config.py`

**Purpose**: Central location for all AI prompts

**Contains**:

- `SQL_GENERATION_PROMPT`: Instructions for generating SQL queries
- `TABLE_SELECTION_PROMPT`: Instructions for selecting relevant tables
- `ANSWER_GENERATION_PROMPT`: Instructions for formatting responses
- `FEW_SHOT_EXAMPLES`: Example question-query pairs for training

**Why separate?**

- ✅ Easy to modify prompts without touching code
- ✅ Version control for prompt changes
- ✅ Team members can update prompts without coding knowledge
- ✅ Quick A/B testing of different prompts

### 2. `database_table_descriptions.csv`

**Purpose**: Source of truth for database schema

**Structure**:

```csv
table_name,description
contacts,"Primary table with student_name, email, phone..."
cases,"Support cases linked via student_name..."
```

**When to update**:

- ✅ Adding new tables to database
- ✅ Changing table relationships
- ✅ Adding/removing columns
- ✅ Updating table purposes

---

## How to Modify Prompts

### Changing SQL Generation Rules

**File**: `prompts_config.py`  
**Section**: `SQL_GENERATION_PROMPT`

**Example**: Add a new rule about handling NULL values

```python
IMPORTANT RULES:
1. **Always use table aliases** for clarity
2. **Join through proper relationships**
3. **Handle NULL values**: Use COALESCE or IS NULL checks  # NEW RULE
...
```

### Adding New Term Mappings

**File**: `prompts_config.py`  
**Section**: `SQL_GENERATION_PROMPT` → **Common terms mapping**

```python
4. **Common terms mapping**:
   - "customer" or "user" → contacts table
   - "student" → contacts table (student_name field)
   - "invoice" → orders table  # NEW MAPPING
```

### Adding Training Examples

**File**: `prompts_config.py`  
**Section**: `FEW_SHOT_EXAMPLES`

```python
FEW_SHOT_EXAMPLES = [
    # ... existing examples ...
    {
        "input": "Show me students who enrolled this month",
        "query": "SELECT * FROM contacts WHERE created_date >= DATE_TRUNC('month', NOW());"
    }
]
```

**Best practices for examples**:

- Use actual table and column names
- Cover different query types (simple, joins, aggregations)
- Include edge cases (orphan records, NULL handling)
- Keep queries syntactically correct

### Changing Response Style

**File**: `prompts_config.py`  
**Section**: `ANSWER_GENERATION_PROMPT`

**Example**: Make responses more technical

```python
Guidelines:
- Respond in a natural, human-like way
- Include technical details like query execution time  # NEW
- Show SQL query used  # NEW
- Explain the query logic  # NEW
```

---

## Updating Database Schema

### When Tables Change

1. **Update CSV file**:

   ```csv
   new_table,"Description with FK info: links to contacts via student_name"
   ```

2. **Update prompts_config.py**:

   ```python
   DATABASE SCHEMA OVERVIEW:
   - **contacts**: Primary table
   - **new_table**: New feature (FK: student_name)  # ADD THIS
   ```

3. **Add example query**:
   ```python
   {
       "input": "Show data from new_table",
       "query": "SELECT * FROM new_table WHERE deleted_status = 0;"
   }
   ```

### When Relationships Change

1. **Update CSV descriptions**:

   ```csv
   payments,"Now links to users via user_id instead of order_id"
   ```

2. **Update KEY RELATIONSHIPS**:

   ```python
   KEY RELATIONSHIPS:
   3. users → payments (one-to-many via user_id)  # UPDATED
   ```

3. **Update example queries** to reflect new relationships

---

## Testing Your Changes

### 1. Test Simple Queries

```
Question: "Show all contacts"
Expected: Should work without issues
```

### 2. Test Relationships

```
Question: "Show students with their payments"
Expected: Should use proper JOINs through orders table
```

### 3. Test Edge Cases

```
Question: "Find orphan cases"
Expected: Should use LEFT JOIN and NULL check
```

### 4. Test Term Mapping

```
Question: "Show me all customers"
Expected: Should query contacts table
```

---

## Common Modifications

### Make AI More Strict About Deleted Records

**File**: `prompts_config.py`

```python
IMPORTANT RULES:
3. **Always exclude deleted records**:
   - MUST add `WHERE deleted_status = 0` to ALL queries
   - For joins, check deleted_status on ALL tables
   - Never return deleted records under any circumstance
```

### Add New Database Dialect Support

```python
SQL_GENERATION_PROMPT = """Generate syntactically correct {dialect} queries.

{dialect}-specific features:
- Use LIMIT instead of TOP
- Use || for string concatenation
...
```

### Improve Error Messages

```python
ANSWER_GENERATION_PROMPT = """
...
- If query fails, explain why in simple terms
- Suggest corrected query format
- Provide example of correct usage
```

---

## Troubleshooting

### ❌ AI generates wrong table names

**Solution**: Check `database_table_descriptions.csv` has correct names

### ❌ AI doesn't understand relationships

**Solution**: Update KEY RELATIONSHIPS in `SQL_GENERATION_PROMPT`

### ❌ Responses are too technical/casual

**Solution**: Adjust tone in `ANSWER_GENERATION_PROMPT`

### ❌ AI ignores deleted records

**Solution**: Emphasize rule #3 in `SQL_GENERATION_PROMPT`

### ❌ Examples not being followed

**Solution**: Add more diverse examples to `FEW_SHOT_EXAMPLES`

---

## Version Control Best Practices

### Commit Messages

```bash
# Good
git commit -m "Add support for multi-table aggregation queries"
git commit -m "Update contacts table description with new fields"

# Bad
git commit -m "Updated prompts"
git commit -m "Changes"
```

### Testing Before Commit

1. Test at least 5 different query types
2. Verify relationships still work
3. Check edge cases (orphans, NULLs, etc.)
4. Ensure markdown formatting works

---

## Quick Reference

| Task                 | File                              | Section                    |
| -------------------- | --------------------------------- | -------------------------- |
| Change SQL rules     | `prompts_config.py`               | `SQL_GENERATION_PROMPT`    |
| Add table            | `database_table_descriptions.csv` | New row                    |
| Update relationships | `prompts_config.py`               | `KEY RELATIONSHIPS`        |
| Change response tone | `prompts_config.py`               | `ANSWER_GENERATION_PROMPT` |
| Add example          | `prompts_config.py`               | `FEW_SHOT_EXAMPLES`        |
| Map new term         | `prompts_config.py`               | `Common terms mapping`     |

---

## Need Help?

1. Check `DATABASE_SCHEMA.md` for current schema
2. Review `FEW_SHOT_EXAMPLES` for patterns
3. Test changes incrementally
4. Keep prompts concise and clear

**Remember**: The AI follows these prompts exactly, so be specific and provide clear examples!
