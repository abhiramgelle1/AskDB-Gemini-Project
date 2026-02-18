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
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>AskOGMS</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-deep: #0a0f1a;
            --bg-mid: #111827;
            --accent: #6366f1;
            --accent-light: #818cf8;
            --accent-glow: rgba(99, 102, 241, 0.35);
            --surface: rgba(255,255,255,0.03);
            --surface-border: rgba(255,255,255,0.08);
            --text: #f1f5f9;
            --text-muted: #94a3b8;
            --user-bubble: linear-gradient(135deg, #4f46e5 0%, #6366f1 50%, #818cf8 100%);
            --bot-bubble: rgba(30,41,59,0.6);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Outfit', -apple-system, sans-serif;
            background: var(--bg-deep);
            min-height: 100vh;
            color: var(--text);
            line-height: 1.6;
            overflow: hidden;
        }
        .bg-canvas {
            position: fixed;
            inset: 0;
            z-index: 0;
            background:
                radial-gradient(ellipse 80% 50% at 20% 40%, rgba(99,102,241,0.15) 0%, transparent 50%),
                radial-gradient(ellipse 60% 40% at 80% 60%, rgba(139,92,246,0.1) 0%, transparent 50%),
                radial-gradient(ellipse 100% 100% at 50% 50%, rgba(15,23,42,0.9) 0%, var(--bg-deep) 100%);
            animation: bgPulse 8s ease-in-out infinite;
        }
        @keyframes bgPulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.85; }
        }
        .grid-overlay {
            position: fixed;
            inset: 0;
            z-index: 0;
            background-image: linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
            background-size: 48px 48px;
            pointer-events: none;
        }

        .topbar {
            position: relative;
            z-index: 10;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.875rem 1.5rem;
            background: rgba(10,15,26,0.7);
            border-bottom: 1px solid var(--surface-border);
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            transition: background 0.3s ease;
        }
        .topbar h1 {
            font-size: clamp(1.1rem, 2.2vw, 1.35rem);
            font-weight: 700;
            letter-spacing: -0.03em;
            background: linear-gradient(135deg, #fff 0%, #c7d2fe 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }
        .topbar a {
            color: var(--text-muted);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            padding: 0.5rem 1rem;
            border-radius: 10px;
            border: 1px solid var(--surface-border);
            transition: all 0.25s ease;
        }
        .topbar a:hover {
            color: var(--accent-light);
            border-color: rgba(99,102,241,0.4);
            background: rgba(99,102,241,0.08);
            transform: translateY(-1px);
        }

        .main {
            position: relative;
            z-index: 5;
            width: 100%;
            max-width: 900px;
            margin: 0 auto;
            padding: clamp(0.75rem, 2vw, 1.25rem);
            height: calc(100vh - 56px);
            display: flex;
            flex-direction: column;
            animation: mainReveal 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        @keyframes mainReveal {
            from { opacity: 0; transform: translateY(16px) scale(0.98); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }

        .card {
            flex: 1;
            min-height: 0;
            display: flex;
            flex-direction: column;
            background: rgba(17,24,39,0.5);
            border: 1px solid var(--surface-border);
            border-radius: 20px;
            overflow: hidden;
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            box-shadow: 0 24px 64px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.05);
            animation: cardFloat 0.8s cubic-bezier(0.22, 1, 0.36, 1) 0.2s both;
        }
        @keyframes cardFloat {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1.25rem 1.5rem;
            min-height: 0;
            display: flex;
            flex-direction: column;
            gap: 1.25rem;
            scroll-behavior: smooth;
        }
        .messages::-webkit-scrollbar { width: 8px; }
        .messages::-webkit-scrollbar-track { background: transparent; }
        .messages::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 4px; }

        .welcome {
            flex: 1;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem 1.5rem;
            text-align: center;
            animation: welcomeIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.3s both;
        }
        @keyframes welcomeIn {
            from { opacity: 0; transform: translateY(12px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .welcome.hidden { display: none; }
        .welcome-icon {
            width: 64px;
            height: 64px;
            margin-bottom: 1.25rem;
            background: var(--user-bubble);
            border-radius: 18px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.75rem;
            box-shadow: 0 12px 32px var(--accent-glow);
            animation: iconBreathe 3s ease-in-out infinite;
        }
        @keyframes iconBreathe {
            0%, 100% { transform: scale(1); box-shadow: 0 12px 32px var(--accent-glow); }
            50% { transform: scale(1.02); box-shadow: 0 16px 40px rgba(99,102,241,0.45); }
        }
        .welcome h2 {
            font-size: clamp(1.15rem, 2.5vw, 1.4rem);
            font-weight: 600;
            color: var(--text);
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        .welcome p {
            color: var(--text-muted);
            font-size: 0.95rem;
            max-width: 320px;
            margin-bottom: 1.5rem;
        }
        .chips {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: center;
        }
        .chip {
            padding: 0.5rem 1rem;
            background: var(--surface);
            border: 1px solid var(--surface-border);
            border-radius: 999px;
            color: var(--text-muted);
            font-size: 0.875rem;
            font-family: inherit;
            cursor: pointer;
            transition: all 0.25s ease;
        }
        .chip:hover {
            color: var(--accent-light);
            border-color: rgba(99,102,241,0.5);
            background: rgba(99,102,241,0.1);
            transform: translateY(-2px);
        }

        .message-row {
            display: flex;
            gap: 0.75rem;
            align-items: flex-end;
            max-width: 85%;
            animation: msgSlide 0.4s cubic-bezier(0.22, 1, 0.36, 1) forwards;
        }
        @keyframes msgSlide {
            from { opacity: 0; transform: translateY(14px) scale(0.96); }
            to { opacity: 1; transform: translateY(0) scale(1); }
        }
        .message-row.user { margin-left: auto; flex-direction: row-reverse; }
        .message-avatar {
            width: 32px;
            height: 32px;
            border-radius: 10px;
            flex-shrink: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.85rem;
            font-weight: 600;
        }
        .message-row.user .message-avatar {
            background: var(--user-bubble);
            color: #fff;
        }
        .message-row.bot .message-avatar {
            background: rgba(51,65,85,0.8);
            color: #c7d2fe;
        }
        .message {
            padding: 1rem 1.25rem;
            border-radius: 16px;
            font-size: 0.9375rem;
            line-height: 1.55;
            word-wrap: break-word;
        }
        .message-row.user .message {
            background: var(--user-bubble);
            color: #fff;
            border-bottom-right-radius: 4px;
            box-shadow: 0 8px 24px rgba(79,70,229,0.35);
        }
        .message-row.bot .message {
            background: var(--bot-bubble);
            border: 1px solid var(--surface-border);
            color: var(--text);
            border-bottom-left-radius: 4px;
        }
        .message-row .message {
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .message-row:hover .message {
            transform: translateY(-1px);
        }
        .message-row.user:hover .message { box-shadow: 0 12px 28px rgba(79,70,229,0.4); }

        .typing-wrap {
            display: none;
            align-items: center;
            gap: 0.75rem;
            padding: 0.5rem 0;
            animation: msgSlide 0.35s ease-out;
        }
        .typing-wrap.show { display: flex; }
        .typing-dots {
            display: flex;
            gap: 5px;
            padding: 1rem 1.25rem;
            background: var(--bot-bubble);
            border: 1px solid var(--surface-border);
            border-radius: 16px;
            border-bottom-left-radius: 4px;
        }
        .typing-dots span {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: var(--text-muted);
            animation: typingBounce 1.2s ease-in-out infinite;
        }
        .typing-dots span:nth-child(2) { animation-delay: 0.15s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.3s; }
        @keyframes typingBounce {
            0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
            30% { transform: translateY(-6px); opacity: 1; }
        }

        .input-area {
            padding: 1rem 1.25rem 1.25rem;
            border-top: 1px solid var(--surface-border);
            background: rgba(10,15,26,0.4);
            flex-shrink: 0;
        }
        .input-wrap {
            display: flex;
            gap: 0.75rem;
            align-items: center;
            padding: 0.5rem;
            background: rgba(255,255,255,0.04);
            border: 1px solid var(--surface-border);
            border-radius: 16px;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .input-wrap:focus-within {
            border-color: rgba(99,102,241,0.5);
            box-shadow: 0 0 0 3px rgba(99,102,241,0.15);
        }
        .input-wrap input {
            flex: 1;
            min-width: 0;
            padding: 0.875rem 1rem;
            background: transparent;
            border: none;
            color: var(--text);
            font-size: 0.9375rem;
            font-family: inherit;
        }
        .input-wrap input::placeholder { color: var(--text-muted); }
        .input-wrap input:focus { outline: none; }
        .input-wrap button {
            padding: 0.75rem 1.25rem;
            background: var(--user-bubble);
            color: #fff;
            border: none;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            font-family: inherit;
            transition: all 0.25s ease;
            box-shadow: 0 4px 14px rgba(79,70,229,0.4);
        }
        .input-wrap button:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(79,70,229,0.5);
        }
        .input-wrap button:active:not(:disabled) { transform: translateY(0); }
        .input-wrap button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }

        @media (max-width: 640px) {
            .main { padding: 0.5rem; height: calc(100vh - 52px); }
            .card { border-radius: 16px; }
            .messages { padding: 1rem; }
            .message-row { max-width: 95%; }
            .welcome { padding: 1.5rem 1rem; }
            .chips { gap: 0.4rem; }
            .chip { padding: 0.4rem 0.85rem; font-size: 0.8125rem; }
        }
    </style>
</head>
<body>
    <div class="bg-canvas"></div>
    <div class="grid-overlay"></div>
    <header class="topbar">
        <h1>AskOGMS</h1>
        <a href="/tables">Schema</a>
    </header>

    <main class="main">
        <div class="card">
            <div class="messages" id="messages"></div>
            <div class="welcome" id="welcome">
                <div class="welcome-icon">Q</div>
                <h2>Ask your data</h2>
                <p>Ask questions in plain English and get answers from your OGMS database.</p>
                <div class="chips">
                    <button type="button" class="chip" data-q="What is the panther id and details of a student?">Panther ID / student details</button>
                    <button type="button" class="chip" data-q="Show appointments for a student for the semester">Appointments for semester</button>
                    <button type="button" class="chip" data-q="What are the speed types of appointment?">Speed types of appointment</button>
                    <button type="button" class="chip" data-q="Total for student funding by university for a specific speedtype">Speedtype total for student funding</button>
                    <button type="button" class="chip" data-q="Who is the advisor of a student?">Advisor of student</button>
                </div>
            </div>
            <div class="typing-wrap" id="typing">
                <div class="message-avatar">A</div>
                <div class="typing-dots"><span></span><span></span><span></span></div>
            </div>
            <div class="input-area">
                <div class="input-wrap">
                    <input type="text" id="input" placeholder="Ask a question..." onkeypress="if(event.key==='Enter') ask()">
                    <button type="button" onclick="ask()" id="btn">Ask</button>
                </div>
            </div>
        </div>
    </main>

    <script>
        var welcome = document.getElementById('welcome');
        var messagesEl = document.getElementById('messages');
        var typingEl = document.getElementById('typing');
        var inputEl = document.getElementById('input');
        var btnEl = document.getElementById('btn');

        document.querySelectorAll('.chip').forEach(function(chip) {
            chip.onclick = function() {
                var q = this.getAttribute('data-q');
                if (q) { inputEl.value = q; ask(); }
            };
        });

        function scrollToBottom() {
            messagesEl.scrollTop = messagesEl.scrollHeight;
        }

        function addMsg(text, type) {
            if (welcome && welcome.classList) welcome.classList.add('hidden');
            var row = document.createElement('div');
            row.className = 'message-row ' + type;
            var avatar = type === 'user' ? 'You' : 'OGMS';
            row.innerHTML = '<div class="message-avatar">' + avatar.charAt(0) + '</div><div class="message">' + escapeHtml(text) + '</div>';
            messagesEl.appendChild(row);
            scrollToBottom();
        }
        function escapeHtml(s) {
            var d = document.createElement('div');
            d.textContent = s;
            return d.innerHTML;
        }

        function setTyping(show) {
            if (show) {
                if (welcome && welcome.classList) welcome.classList.add('hidden');
                typingEl.classList.add('show');
            } else typingEl.classList.remove('show');
            scrollToBottom();
        }

        function ask() {
            var text = inputEl.value.trim();
            if (!text) return;
            addMsg(text, 'user');
            inputEl.value = '';
            setTyping(true);
            btnEl.disabled = true;

            fetch('/api', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question: text })
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                setTyping(false);
                if (data.answer) {
                    var a = data.answer;
                    var txt = typeof a === 'string' ? a : (a && (a.text || a.content)) || JSON.stringify(a);
                    addMsg(txt, 'bot');
                } else if (data.error) addMsg('Error: ' + data.error, 'bot');
            })
            .catch(function(err) {
                setTyping(false);
                addMsg('Error: ' + err.message, 'bot');
            })
            .finally(function() { btnEl.disabled = false; });
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
