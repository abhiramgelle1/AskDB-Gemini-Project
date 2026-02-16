# AskDB setup – PostgreSQL ogms

## 1. Prerequisites

- **Python 3.8+**
- **PostgreSQL** with database **ogms** (you can create it with `CREATE DATABASE ogms;`)
- **Google AI API key:** https://aistudio.google.com/apikey

## 2. Steps

```powershell
# From project folder
cd C:\Users\abhir\Documents\vs-workspace\AskDB

# Install
pip install -r requirements.txt

# Create .env
copy .env.example .env

# Edit .env (Notepad or VS Code)
notepad .env
```

In `.env` set at least:

- `GOOGLE_API_KEY=` your key from aistudio.google.com
- `DB_HOST=` (e.g. `localhost` or your server IP)
- `DB_PORT=5432`
- `DB_NAME=ogms`
- `DB_USER=` your Postgres user
- `DB_PASSWORD=` your Postgres password

Then:

```powershell
# Pull your table list from ogms into database_table_descriptions.csv
python generate_table_descriptions.py

# Edit database_table_descriptions.csv – add a short description for each table (what it stores)
# Then run the app
python code1.py
```

Open http://127.0.0.1:5000 and test with a question about your data.

## 3. Optional

- **LangChain tracing:** Set `LANGCHAIN_TRACING_V2=true` and `LANGCHAIN_API_KEY=` in `.env` to use LangSmith.
- **View raw data:** http://127.0.0.1:5000/view-data
