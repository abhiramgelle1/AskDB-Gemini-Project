from query_engine import chain_code
from langchain_community.chat_message_histories import ChatMessageHistory
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import os
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
    <title>AskDB</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            padding: 20px;
            max-width: 900px;
            margin: 0 auto;
        }
        h1 {
            margin-bottom: 10px;
            color: #333;
            font-size: 24px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        .chat-container {
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            height: 500px;
            display: flex;
            flex-direction: column;
        }
        .messages {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
        }
        .message {
            margin-bottom: 15px;
            padding: 10px 15px;
            border-radius: 4px;
            max-width: 75%;
            word-wrap: break-word;
        }
        .user-message {
            background: #007bff;
            color: white;
            margin-left: auto;
        }
        .bot-message {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            margin-right: auto;
        }
        .input-area {
            display: flex;
            padding: 15px;
            border-top: 1px solid #ddd;
        }
        .input-area input {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .input-area button {
            margin-left: 10px;
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
        }
        .input-area button:hover { background: #0056b3; }
        .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
            font-size: 14px;
        }
        .loading.show { display: block; }
        .error { color: #dc3545; }
        .links {
            margin-top: 20px;
            text-align: center;
        }
        .links a {
            color: #007bff;
            text-decoration: none;
            margin: 0 15px;
            font-size: 14px;
        }
        .links a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h1>AskDB</h1>
    <div class="subtitle">Query your database in natural language</div>
    
    <div class="chat-container">
        <div class="messages" id="messages"></div>
        <div class="loading" id="loading">Processing...</div>
        <div class="input-area">
            <input type="text" id="input" placeholder="Ask a question..." onkeypress="if(event.key==='Enter') ask()">
            <button onclick="ask()" id="btn">Ask</button>
        </div>
    </div>
    
    <div class="links">
        <a href="/view-data" target="_blank">View Database</a>
        <a href="/api" target="_blank">API</a>
    </div>

    <script>
        function addMsg(text, type) {
            const div = document.createElement('div');
            div.className = 'message ' + type + '-message';
            div.textContent = text;
            document.getElementById('messages').appendChild(div);
            document.getElementById('messages').scrollTop = document.getElementById('messages').scrollHeight;
        }
        
        function ask() {
            const input = document.getElementById('input');
            const text = input.value.trim();
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
            .then(r => r.json())
            .then(data => {
                document.getElementById('loading').classList.remove('show');
                if (data.answer) {
                    const a = data.answer;
                    const txt = typeof a === 'string' ? a : (a?.text || a?.content || JSON.stringify(a));
                    addMsg(txt, 'bot');
                } else if (data.error) {
                    addMsg('Error: ' + data.error, 'bot');
                }
            })
            .catch(err => {
                document.getElementById('loading').classList.remove('show');
                addMsg('Error: ' + err.message, 'bot');
            })
            .finally(() => {
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

@app.route('/view-data')
def view_data():
    try:
        load_dotenv()
        db_type = os.getenv("DB_TYPE", "postgresql")
        
        if db_type.lower() == "postgresql":
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "ogms")
            )
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [t[0] for t in cursor.fetchall()]
            
            table_data = {}
            for table in tables:
                cursor.execute(f'SELECT * FROM {table} LIMIT 100')
                rows = cursor.fetchall()
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
                columns = [c[0] for c in cursor.fetchall()]
                table_data[table] = {'columns': columns, 'rows': rows}
            
            conn.close()
        else:
            import sqlite3
            conn = sqlite3.connect(os.getenv("DB_NAME", "askdb_local.db"))
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
            tables = [t[0] for t in cursor.fetchall()]
            
            table_data = {}
            for table in tables:
                cursor.execute(f'SELECT * FROM {table} LIMIT 100')
                rows = cursor.fetchall()
                cursor.execute(f'PRAGMA table_info({table})')
                columns = [c[1] for c in cursor.fetchall()]
                table_data[table] = {'columns': columns, 'rows': rows}
            
            conn.close()
        
        html = "<html><head><title>Database View</title><style>body{font-family:monospace;padding:20px;}table{border-collapse:collapse;margin:20px 0;}th,td{border:1px solid #ddd;padding:8px;}th{background:#f0f0f0;}</style></head><body><h1>Database Tables</h1>"
        for table, data in table_data.items():
            html += f"<h2>{table}</h2><table><tr>"
            for col in data['columns']:
                html += f"<th>{col}</th>"
            html += "</tr>"
            for row in data['rows']:
                html += "<tr>"
                for val in row:
                    html += f"<td>{val}</td>"
                html += "</tr>"
            html += "</table>"
        html += "</body></html>"
        return html
        
    except Exception as e:
        return f"<html><body>Error: {str(e)}</body></html>", 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
