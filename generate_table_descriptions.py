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

conn = psycopg2.connect(
    host=host, port=port, dbname=dbname, user=user, password=password
)
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
