# AskDB – Natural language to SQL (PostgreSQL)

Ask questions in plain English; get answers from your **PostgreSQL `ogms`** database.

## What you need

- Python 3.8+
- PostgreSQL with your **ogms** database
- **Google AI API key** from https://aistudio.google.com/apikey

## Setup (once)

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure `.env`**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and set:
   - `GOOGLE_API_KEY` = your Google API key
   - `DB_HOST`, `DB_PORT`, `DB_NAME=ogms`, `DB_USER`, `DB_PASSWORD` for your Postgres

3. **Generate table descriptions from your ogms DB**
   ```bash
   python generate_table_descriptions.py
   ```
   This creates/overwrites `database_table_descriptions.csv` with your tables.  
   Open the CSV and add a short **description** for each table (what it stores, main columns). Save.

## Run

```bash
python code1.py
```

Open **http://127.0.0.1:5000** — ask questions in natural language and get answers from ogms.

- **API:** `POST http://localhost:5000/api` with JSON `{"question": "your question?"}`
- **View data:** http://127.0.0.1:5000/view-data

## Project layout

| File | Purpose |
|------|--------|
| `code1.py` | Flask app (UI + API) |
| `untitled0.py` | DB connection + LangChain/Gemini query engine |
| `prompts_config.py` | Prompts for SQL generation |
| `.env` | Your secrets (create from `.env.example`) |
| `database_table_descriptions.csv` | Table list + descriptions (from `generate_table_descriptions.py`) |

## Troubleshooting

- **Database connection failed** – Check `DB_*` in `.env` (host, port, user, password, dbname=ogms).
- **Wrong or no tables** – Run `python generate_table_descriptions.py` again and fix `database_table_descriptions.csv`.
- **GOOGLE_API_KEY error** – Set it in `.env` and restart the app.
- **429 RESOURCE_EXHAUSTED / quota exceeded** – Free-tier limits reached. In `.env` try `GEMINI_MODEL=gemini-3-flash-preview` (separate quota), or set up billing in [Google AI Studio](https://aistudio.google.com/app/api-keys). See [rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).
- **404 NOT_FOUND (model not found)** – Some model IDs (e.g. `gemini-1.5-flash-001`) are not available for all keys. Use `GEMINI_MODEL=gemini-2.0-flash` or `gemini-3-flash-preview`.
