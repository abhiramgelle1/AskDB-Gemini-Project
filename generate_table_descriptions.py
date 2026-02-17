"""
Generate database_table_descriptions.csv from your PostgreSQL ogms database.
Run once: python generate_table_descriptions.py
Then edit the CSV and add a short description for each table (what it stores, main columns).
"""
import os
import csv
from dotenv import load_dotenv

load_dotenv()

host = os.getenv("DB_HOST", "localhost")
port = os.getenv("DB_PORT", "5432")
dbname = os.getenv("DB_NAME", "ogms")
user = os.getenv("DB_USER", "postgres")
password = os.getenv("DB_PASSWORD", "")

try:
    import psycopg2
except ImportError:
    print("Install: pip install psycopg2-binary")
    raise

if not password and os.getenv("DB_PASSWORD") is None:
    print("ERROR: No .env or DB_PASSWORD not set.")
    print("  1. Copy .env.example to .env:  copy .env.example .env")
    print("  2. Edit .env and set your Postgres credentials:")
    print("     DB_USER=your_postgres_username")
    print("     DB_PASSWORD=your_postgres_password")
    print("     DB_NAME=ogms")
    print("     (and DB_HOST if not localhost)")
    raise SystemExit(1)

try:
    conn = psycopg2.connect(
        host=host, port=port, dbname=dbname, user=user, password=password
    )
except Exception as e:
    print("PostgreSQL connection failed:", e)
    print()
    print("Check your .env file (copy from .env.example if missing):")
    print("  DB_HOST=" + host)
    print("  DB_PORT=" + port)
    print("  DB_NAME=" + dbname)
    print("  DB_USER=" + user)
    print("  DB_PASSWORD=(must be your actual Postgres password)")
    raise SystemExit(1)

cur = conn.cursor()
cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
tables = [row[0] for row in cur.fetchall()]
conn.close()

out = "database_table_descriptions.csv"
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["table_name", "description"])
    for t in tables:
        w.writerow([t, "Describe this table (columns, purpose)."])

print(f"Wrote {out} with {len(tables)} tables. Edit the description column for each table, then run: python code1.py")
