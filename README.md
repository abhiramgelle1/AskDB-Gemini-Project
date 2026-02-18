# AskDB

Natural language to SQL query system for PostgreSQL databases.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env`:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
- `GOOGLE_API_KEY` - Required. Get from https://aistudio.google.com/apikey
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - PostgreSQL connection
- `GEMINI_MODEL` - Model name (default: `gemini-2.0-flash`)
- `GEMINI_TIMEOUT` - Timeout in seconds (default: 90)

3. Generate table descriptions:
```bash
python generate_table_descriptions.py
```

Edit `database_table_descriptions.csv` and add descriptions for each table.

4. Run:
```bash
python app.py
```

Open http://127.0.0.1:5000

## API

POST `/api` with JSON body:
```json
{"question": "your question"}
```

Returns:
```json
{"answer": "response text"}
```

## Files

- `app.py` - Flask web server
- `query_engine.py` - Core query processing logic
- `prompts_config.py` - LLM prompts
- `generate_table_descriptions.py` - Generate table descriptions CSV
- `database_table_descriptions.csv` - Table metadata (edit after generation)

## Troubleshooting

- **429 RESOURCE_EXHAUSTED** - Quota exceeded. Try `GEMINI_MODEL=gemini-3-flash-preview` or set up billing.
- **404 NOT_FOUND** - Model not available. Use `gemini-2.0-flash` or `gemini-3-flash-preview`.
- **504 DEADLINE_EXCEEDED** - Increase `GEMINI_TIMEOUT=120` in `.env`.
- **Database connection failed** - Check `DB_*` settings in `.env`.
