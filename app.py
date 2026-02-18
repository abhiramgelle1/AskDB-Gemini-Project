from query_engine import chain_code
from langchain_community.chat_message_histories import ChatMessageHistory
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
import csv
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app)

history = ChatMessageHistory()

@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskOGMS</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 35%, #334155 70%, #1e293b 100%);
            background-size: 200% 200%;
            animation: bgShift 12s ease infinite;
            min-height: 100vh;
            color: #e2e8f0;
            line-height: 1.5;
        }
        @keyframes bgShift {
            0%, 100% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
        }

        .topbar {
            background: linear-gradient(90deg, rgba(15,23,42,0.92) 0%, rgba(30,41,59,0.92) 100%);
            color: #f8fafc;
            padding: 0.75rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 24px rgba(0,0,0,0.25);
            backdrop-filter: blur(10px);
            transition: box-shadow 0.3s ease;
        }
        .topbar:hover { box-shadow: 0 6px 28px rgba(0,0,0,0.3); }
        .topbar h1 { font-size: 1.25rem; font-weight: 600; letter-spacing: -0.02em; }
        .topbar a {
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: background 0.25s ease, color 0.25s ease, transform 0.2s ease;
        }
        .topbar a:hover { background: #1e293b; color: #f8fafc; transform: translateY(-1px); }

        .main {
            width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 1rem 1.25rem;
            height: calc(100vh - 52px);
            display: flex;
            flex-direction: column;
            animation: mainIn 0.4s ease-out;
        }
        @keyframes mainIn {
            from { opacity: 0; transform: translateY(8px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .card {
            background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
            border-radius: 16px;
            box-shadow: 0 12px 48px rgba(0,0,0,0.22), 0 0 0 1px rgba(255,255,255,0.12);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            flex: 1;
            min-height: 0;
            transition: box-shadow 0.3s ease, transform 0.3s ease;
        }
        .card:hover { box-shadow: 0 16px 56px rgba(0,0,0,0.25), 0 0 0 1px rgba(255,255,255,0.12); }

        .messages {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1.25rem 1.5rem;
            min-height: 0;
            display: flex;
            flex-direction: column;
            gap: 1rem;
            scroll-behavior: smooth;
        }

        .message {
            padding: 1rem 1.25rem;
            border-radius: 14px;
            max-width: 75%;
            word-wrap: break-word;
            font-size: 0.9375rem;
            line-height: 1.55;
            flex-shrink: 0;
            animation: msgIn 0.35s ease-out;
        }
        @keyframes msgIn {
            from { opacity: 0; transform: translateY(10px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .user-message {
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
            color: #f8fafc;
            margin-left: auto;
            box-shadow: 0 4px 16px rgba(15,23,42,0.35);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .user-message:hover { transform: translateX(-2px); box-shadow: 0 6px 20px rgba(15,23,42,0.4); }

        .bot-message {
            background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
            border: 1px solid #e2e8f0;
            margin-right: auto;
            color: #334155;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .bot-message:hover { transform: translateX(2px); box-shadow: 0 4px 16px rgba(0,0,0,0.06); }

        .input-wrap {
            padding: 1rem 1.5rem 1.25rem;
            border-top: 1px solid #e2e8f0;
            background: linear-gradient(180deg, #fff 0%, #f8fafc 100%);
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex-shrink: 0;
            transition: background 0.2s ease;
        }

        .input-wrap input {
            flex: 1;
            min-width: 0;
            padding: 0.875rem 1.25rem;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            font-size: 0.9375rem;
            font-family: inherit;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .input-wrap input::placeholder { color: #94a3b8; }
        .input-wrap input:focus {
            outline: none;
            border-color: #0f172a;
            box-shadow: 0 0 0 3px rgba(15,23,42,0.08);
        }

        .input-wrap button {
            padding: 0.875rem 1.5rem;
            background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
            color: #f8fafc;
            border: none;
            border-radius: 12px;
            font-size: 0.9375rem;
            font-weight: 500;
            cursor: pointer;
            font-family: inherit;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            flex-shrink: 0;
            box-shadow: 0 4px 14px rgba(15,23,42,0.3);
        }
        .input-wrap button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(15,23,42,0.4);
        }
        .input-wrap button:active:not(:disabled) { transform: translateY(0); }
        .input-wrap button:disabled { opacity: 0.6; cursor: not-allowed; }

        .loading {
            display: none;
            text-align: center;
            padding: 1rem 1.25rem;
            color: #64748b;
            font-size: 0.875rem;
        }
        .loading.show {
            display: block;
            animation: pulse 1.2s ease-in-out infinite;
        }
        @keyframes pulse { 0%, 100% { opacity: 0.7; } 50% { opacity: 1; } }

        @media (min-width: 900px) {
            .main { padding: 1.25rem 1.5rem; }
            .message { max-width: 65%; }
        }
        @media (max-width: 640px) {
            .main { padding: 0.75rem 0.75rem; height: calc(100vh - 50px); }
            .card { border-radius: 14px; }
            .messages { padding: 1rem; }
            .message { max-width: 92%; padding: 0.875rem 1rem; }
            .input-wrap { padding: 0.875rem 1rem; }
            .input-wrap input { padding: 0.75rem 1rem; }
            .input-wrap button { padding: 0.75rem 1.25rem; }
        }
    </style>
</head>
<body>
    <header class="topbar">
        <h1>AskOGMS</h1>
        <a href="/tables">Table descriptions</a>
    </header>

    <main class="main">
        <div class="card">
            <div class="messages" id="messages"></div>
            <div class="loading" id="loading">Processing...</div>
            <div class="input-wrap">
                <input type="text" id="input" placeholder="Ask a question about your data..." onkeypress="if(event.key==='Enter') ask()">
                <button type="button" onclick="ask()" id="btn">Ask</button>
            </div>
        </div>
    </main>

    <script>
        function addMsg(text, type) {
            var div = document.createElement('div');
            div.className = 'message ' + type + '-message';
            div.textContent = text;
            document.getElementById('messages').appendChild(div);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }

        function ask() {
            var input = document.getElementById('input');
            var text = input.value.trim();
            if (!text) return;

            addMsg(text, 'user');
            input.value = '';
            document.getElementById('loading').classList.add('show');
            document.getElementById('btn').disabled = true;

            fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                document.getElementById('loading').classList.remove('show');
                if (data.answer) {
                    var a = data.answer;
                    var txt = typeof a === 'string' ? a : (a && (a.text || a.content)) || JSON.stringify(a);
                    addMsg(txt, 'bot');
                } else if (data.error) {
                    addMsg('Error: ' + data.error, 'bot');
                }
            })
            .catch(function(err) {
                document.getElementById('loading').classList.remove('show');
                addMsg('Error: ' + err.message, 'bot');
            })
            .finally(function() {
                document.getElementById('btn').disabled = false;
            });
        }
    </script>
</body>
</html>
    """)

@app.route('/api', methods=['POST'])
def api():
    try:
        data = request.get_json()
        q = data.get('question')
        if not q:
            return jsonify({"error": "Missing 'question'"}), 400

        history.add_user_message(q)
        formatted_messages = [
            {"role": "user" if msg.type == "user" else "assistant", "content": msg.content}
            for msg in history.messages
        ]

        res = chain_code(q, formatted_messages)

        if isinstance(res, str):
            answer_text = res
        elif isinstance(res, dict):
            answer_text = res.get("text") or res.get("content")
            if not isinstance(answer_text, str):
                answer_text = str(answer_text) if answer_text is not None else str(res)
        else:
            answer_text = str(res) if res is not None else "No response generated."

        history.add_ai_message(answer_text)
        return jsonify({"answer": answer_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _get_db_connection():
    """Return a psycopg2 connection using .env (PostgreSQL only)."""
    load_dotenv()
    import psycopg2
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "ogms"),
    )


@app.route('/api/schema')
def api_schema():
    """Return list of tables, or schema (columns, PK, FK) for one table."""
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        table_name = request.args.get("table")
        schema = "public"

        if not table_name:
            cur.execute("""
                SELECT table_name FROM information_schema.tables
                WHERE table_schema = %s AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (schema,))
            tables = [row[0] for row in cur.fetchall()]
            conn.close()
            return jsonify({"tables": tables})

        # Columns
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position
        """, (schema, table_name))
        columns = [{"name": r[0], "type": r[1], "nullable": r[2] == "YES"} for r in cur.fetchall()]

        # Primary key columns
        cur.execute("""
            SELECT kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            WHERE tc.table_schema = %s AND tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
            ORDER BY kcu.ordinal_position
        """, (schema, table_name))
        pk_columns = [r[0] for r in cur.fetchall()]

        # Foreign keys: column -> (referenced_table, referenced_column)
        cur.execute("""
            SELECT kcu.column_name, ccu.table_name AS ref_table, ccu.column_name AS ref_column
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.table_schema
            WHERE tc.table_schema = %s AND tc.table_name = %s AND tc.constraint_type = 'FOREIGN KEY'
        """, (schema, table_name))
        fk_map = {r[0]: {"table": r[1], "column": r[2]} for r in cur.fetchall()}

        for col in columns:
            col["pk"] = col["name"] in pk_columns
            col["fk"] = fk_map.get(col["name"])

        conn.close()
        return jsonify({"table": table_name, "columns": columns})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/tables')
def table_descriptions():
    """Schema viewer: search tables, show columns with PK/FK."""
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskOGMS - Schema</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'DM Sans', sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 40%, #334155 100%);
            min-height: 100vh;
            color: #e2e8f0;
            line-height: 1.5;
        }
        .topbar {
            background: linear-gradient(90deg, rgba(15,23,42,0.95) 0%, rgba(30,41,59,0.95) 100%);
            color: #f8fafc;
            padding: 0.875rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        .topbar h1 { font-size: 1.25rem; font-weight: 600; }
        .topbar a { color: #94a3b8; text-decoration: none; padding: 0.5rem 1rem; border-radius: 8px; }
        .topbar a:hover { background: #1e293b; color: #f8fafc; }
        .main {
            max-width: 900px;
            margin: 0 auto;
            padding: 1.25rem 1rem;
            min-height: calc(100vh - 56px);
        }
        .search-wrap {
            margin-bottom: 1.25rem;
        }
        .search-wrap input {
            width: 100%;
            padding: 0.75rem 1rem;
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 10px;
            background: rgba(255,255,255,0.08);
            color: #f8fafc;
            font-size: 0.9375rem;
            font-family: inherit;
        }
        .search-wrap input::placeholder { color: #94a3b8; }
        .search-wrap input:focus {
            outline: none;
            border-color: #64748b;
            background: rgba(255,255,255,0.1);
        }
        .table-list {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .table-pill {
            padding: 0.5rem 0.875rem;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 8px;
            color: #e2e8f0;
            font-size: 0.875rem;
            cursor: pointer;
            transition: background 0.2s, border-color 0.2s;
        }
        .table-pill:hover { background: rgba(255,255,255,0.15); border-color: rgba(255,255,255,0.25); }
        .table-pill.selected { background: rgba(30,58,95,0.8); border-color: #3b82f6; color: #f8fafc; }
        .schema-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.98) 0%, rgba(248,250,252,0.98) 100%);
            border-radius: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.2);
            overflow: hidden;
            margin-top: 1rem;
        }
        .schema-card h2 {
            padding: 1rem 1.25rem;
            font-size: 1rem;
            color: #0f172a;
            border-bottom: 1px solid #e2e8f0;
            background: rgba(241,245,249,0.8);
        }
        .schema-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 0.875rem;
        }
        .schema-table th {
            text-align: left;
            padding: 0.625rem 1rem;
            background: #f1f5f9;
            color: #475569;
            font-weight: 600;
        }
        .schema-table td { padding: 0.625rem 1rem; border-bottom: 1px solid #e2e8f0; color: #334155; }
        .schema-table tr:last-child td { border-bottom: none; }
        .schema-table .col-name { font-weight: 500; color: #0f172a; }
        .schema-table .col-type { color: #64748b; font-family: ui-monospace, monospace; }
        .badge { display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.7rem; font-weight: 600; margin-right: 0.25rem; }
        .badge-pk { background: #dbeafe; color: #1d4ed8; }
        .badge-fk { background: #fef3c7; color: #b45309; }
        .badge-null { color: #94a3b8; font-weight: 400; }
        .empty-state { text-align: center; padding: 2rem; color: #94a3b8; font-size: 0.9375rem; }
        .error-msg { padding: 1rem; background: rgba(239,68,68,0.15); border-radius: 10px; color: #fca5a5; margin-top: 1rem; }
        @media (max-width: 640px) {
            .main { padding: 1rem 0.75rem; }
            .schema-table th, .schema-table td { padding: 0.5rem 0.75rem; font-size: 0.8125rem; }
        }
    </style>
</head>
<body>
    <header class="topbar"><h1>AskOGMS</h1><a href="/">Chat</a></header>
    <div class="main">
        <div class="search-wrap">
            <input type="text" id="search" placeholder="Search tables..." oninput="filterTables()">
        </div>
        <div class="table-list" id="tableList"></div>
        <div id="schemaCard"></div>
        <div id="errorMsg" class="error-msg" style="display:none;"></div>
    </div>
    <script>
        var allTables = [];
        var selectedTable = null;

        fetch('/api/schema').then(function(r){ return r.json(); }).then(function(data){
            if (data.error) { document.getElementById('errorMsg').textContent = data.error; document.getElementById('errorMsg').style.display = 'block'; return; }
            allTables = data.tables || [];
            renderTableList(allTables);
        }).catch(function(e){ document.getElementById('errorMsg').textContent = 'Failed to load tables.'; document.getElementById('errorMsg').style.display = 'block'; });

        function renderTableList(tables) {
            var list = document.getElementById('tableList');
            list.innerHTML = tables.map(function(t){
                var sel = t === selectedTable ? ' selected' : '';
                return '<button type="button" class="table-pill' + sel + '" data-table="' + t + '">' + t + '</button>';
            }).join('');
            list.querySelectorAll('.table-pill').forEach(function(btn){
                btn.onclick = function(){ selectTable(btn.getAttribute('data-table')); };
            });
        }

        function filterTables() {
            var q = document.getElementById('search').value.trim().toLowerCase();
            var filtered = q ? allTables.filter(function(t){ return t.toLowerCase().indexOf(q) >= 0; }) : allTables;
            renderTableList(filtered);
        }

        function selectTable(name) {
            selectedTable = name;
            renderTableList(document.getElementById('search').value.trim() ? allTables.filter(function(t){ return t.toLowerCase().indexOf(document.getElementById('search').value.trim().toLowerCase()) >= 0; }) : allTables);
            document.getElementById('errorMsg').style.display = 'none';
            fetch('/api/schema?table=' + encodeURIComponent(name)).then(function(r){ return r.json(); }).then(function(data){
                if (data.error) { document.getElementById('errorMsg').textContent = data.error; document.getElementById('errorMsg').style.display = 'block'; document.getElementById('schemaCard').innerHTML = ''; return; }
                var cols = data.columns || [];
                var html = '<div class="schema-card"><h2>' + name + ' — columns &amp; keys</h2><table class="schema-table"><thead><tr><th>Column</th><th>Type</th><th>Nullable</th><th>Key</th></tr></thead><tbody>';
                cols.forEach(function(c){
                    var keys = [];
                    if (c.pk) keys.push('<span class="badge badge-pk">PK</span>');
                    if (c.fk) keys.push('<span class="badge badge-fk">FK → ' + c.fk.table + '.' + c.fk.column + '</span>');
                    if (!keys.length) keys.push('<span class="badge-null">—</span>');
                    html += '<tr><td class="col-name">' + c.name + '</td><td class="col-type">' + c.type + '</td><td>' + (c.nullable ? 'Yes' : 'No') + '</td><td>' + keys.join(' ') + '</td></tr>';
                });
                html += '</tbody></table></div>';
                document.getElementById('schemaCard').innerHTML = html;
            });
        }
    </script>
</body>
</html>
    """)

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
