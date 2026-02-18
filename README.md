# AskOGMS

Natural language to SQL for PostgreSQL (OGMS database).

## Setup

1. Install:
```bash
pip install -r requirements.txt
```

2. Configure `.env` (copy from `.env.example`):
- `GOOGLE_API_KEY` (required)
- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`

3. Generate table descriptions:
```bash
python generate_table_descriptions.py
```
Edit `database_table_descriptions.csv` and add a short description for each table.

4. Run:
```bash
python app.py
```
Open http://127.0.0.1:5000

## Usage

- **Chat** – Ask questions in natural language on the main page.
- **Table descriptions** – Link on the page shows table name and description (from the CSV).

## Files

- `app.py` – Web server (chat + table descriptions view)
- `query_engine.py` – Query logic
- `prompts_config.py` – LLM prompts
- `generate_table_descriptions.py` – Build `database_table_descriptions.csv`
- `database_table_descriptions.csv` – Table metadata

## Troubleshooting

- **429** – Try `GEMINI_MODEL=gemini-3-flash-preview` or set up billing.
- **404** – Use `GEMINI_MODEL=gemini-2.0-flash` or `gemini-3-flash-preview`.
- **504** – Increase `GEMINI_TIMEOUT=120` in `.env`.
- **DB connection** – Check `DB_*` in `.env`.
