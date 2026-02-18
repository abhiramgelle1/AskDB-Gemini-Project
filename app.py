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
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #e2e8f0;
            min-height: 100vh;
            color: #334155;
            line-height: 1.5;
        }

        .topbar {
            background: #0f172a;
            color: #f8fafc;
            padding: 1rem 1.5rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
        }

        .topbar h1 {
            font-size: 1.25rem;
            font-weight: 600;
            letter-spacing: -0.02em;
        }

        .topbar a {
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.9rem;
            padding: 0.5rem 1rem;
            border-radius: 8px;
            transition: background 0.2s, color 0.2s;
        }

        .topbar a:hover {
            background: #1e293b;
            color: #f8fafc;
        }

        .main {
            max-width: 680px;
            margin: 0 auto;
            padding: 1.5rem 1rem;
        }

        .card {
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
            overflow: hidden;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 120px);
            min-height: 380px;
            max-height: 720px;
        }

        .messages {
            flex: 1;
            overflow-y: auto;
            overflow-x: hidden;
            padding: 1.5rem 1.25rem;
            min-height: 0;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }

        .message {
            padding: 1rem 1.25rem;
            border-radius: 14px;
            max-width: min(88%, 420px);
            word-wrap: break-word;
            font-size: 0.9375rem;
            line-height: 1.55;
            flex-shrink: 0;
        }

        .user-message {
            background: #0f172a;
            color: #f8fafc;
            margin-left: auto;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.2);
        }

        .bot-message {
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            margin-right: auto;
            color: #334155;
        }

        .input-wrap {
            padding: 1rem 1.25rem 1.25rem;
            border-top: 1px solid #e2e8f0;
            background: #fff;
            display: flex;
            gap: 0.75rem;
            align-items: center;
            flex-shrink: 0;
        }

        .input-wrap input {
            flex: 1;
            min-width: 0;
            padding: 0.875rem 1.125rem;
            border: 1px solid #cbd5e1;
            border-radius: 10px;
            font-size: 0.9375rem;
            font-family: inherit;
            transition: border-color 0.2s, box-shadow 0.2s;
        }

        .input-wrap input::placeholder {
            color: #94a3b8;
        }

        .input-wrap input:focus {
            outline: none;
            border-color: #0f172a;
            box-shadow: 0 0 0 3px rgba(15, 23, 42, 0.1);
        }

        .input-wrap button {
            padding: 0.875rem 1.5rem;
            background: #0f172a;
            color: #f8fafc;
            border: none;
            border-radius: 10px;
            font-size: 0.9375rem;
            font-weight: 500;
            cursor: pointer;
            font-family: inherit;
            transition: background 0.2s, opacity 0.2s;
            flex-shrink: 0;
        }

        .input-wrap button:hover {
            background: #1e293b;
        }

        .input-wrap button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .loading {
            display: none;
            text-align: center;
            padding: 1rem 1.25rem;
            color: #64748b;
            font-size: 0.875rem;
        }

        .loading.show {
            display: block;
        }

        @media (max-width: 640px) {
            .main {
                padding: 1rem 0.75rem;
            }

            .card {
                height: calc(100vh - 100px);
                min-height: 320px;
                border-radius: 12px;
            }

            .messages {
                padding: 1rem 1rem;
            }

            .message {
                max-width: 92%;
                padding: 0.875rem 1rem;
            }

            .input-wrap {
                padding: 0.875rem 1rem 1rem;
                flex-wrap: nowrap;
            }

            .input-wrap input {
                padding: 0.75rem 1rem;
            }

            .input-wrap button {
                padding: 0.75rem 1.25rem;
            }
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

@app.route('/tables')
def table_descriptions():
    """Show table name and description from database_table_descriptions.csv."""
    try:
        path = os.path.join(os.path.dirname(__file__), "database_table_descriptions.csv")
        if not os.path.isfile(path):
            return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskOGMS - Table descriptions</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'DM Sans', sans-serif; background: #e2e8f0; min-height: 100vh; color: #334155; }
        .topbar { background: #0f172a; color: #f8fafc; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        .topbar h1 { font-size: 1.25rem; font-weight: 600; }
        .topbar a { color: #94a3b8; text-decoration: none; padding: 0.5rem 1rem; border-radius: 8px; }
        .topbar a:hover { background: #1e293b; color: #f8fafc; }
        .main { max-width: 680px; margin: 0 auto; padding: 1.5rem 1rem; }
        .card { background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 1.5rem 1.5rem; }
        .card h2 { font-size: 1rem; color: #0f172a; margin-bottom: 0.75rem; }
        .card p { color: #64748b; font-size: 0.9375rem; line-height: 1.55; }
        .card a { color: #0f172a; font-weight: 500; margin-top: 1rem; display: inline-block; }
    </style>
</head>
<body>
    <header class="topbar"><h1>AskOGMS</h1><a href="/">Chat</a></header>
    <div class="main">
        <div class="card">
            <h2>Table descriptions</h2>
            <p>No table descriptions file. Run: python generate_table_descriptions.py</p>
            <a href="/">Back to chat</a>
        </div>
    </div>
</body>
</html>""", 200
        rows = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                name = row.get("table_name", "").strip()
                desc = row.get("description", "").strip()
                if name and not name.startswith("_"):
                    rows.append((name, desc))
        html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskOGMS - Table descriptions</title>
    <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'DM Sans', sans-serif; background: #e2e8f0; min-height: 100vh; color: #334155; line-height: 1.5; }
        .topbar { background: #0f172a; color: #f8fafc; padding: 1rem 1.5rem; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.15); }
        .topbar h1 { font-size: 1.25rem; font-weight: 600; }
        .topbar a { color: #94a3b8; text-decoration: none; padding: 0.5rem 1rem; border-radius: 8px; }
        .topbar a:hover { background: #1e293b; color: #f8fafc; }
        .main { max-width: 680px; margin: 0 auto; padding: 1.5rem 1rem; }
        .block { background: #fff; border-radius: 16px; box-shadow: 0 4px 24px rgba(0,0,0,0.08); padding: 1.25rem 1.5rem; margin-bottom: 1rem; }
        .block:last-child { margin-bottom: 0; }
        .block h2 { font-size: 0.9375rem; font-weight: 600; color: #0f172a; margin-bottom: 0.5rem; letter-spacing: -0.01em; }
        .block p { color: #64748b; font-size: 0.9375rem; line-height: 1.55; }
        @media (max-width: 640px) { .main { padding: 1rem 0.75rem; } .block { padding: 1rem 1.25rem; } }
    </style>
</head>
<body>
    <header class="topbar"><h1>AskOGMS</h1><a href="/">Chat</a></header>
    <div class="main">
"""
        for name, desc in rows:
            desc_esc = desc.replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
            html += f'        <div class="block"><h2>{name}</h2><p>{desc_esc}</p></div>\n'
        html += "    </div>\n</body>\n</html>"
        return html
    except Exception as e:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskOGMS</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: system-ui, sans-serif; background: #e2e8f0; padding: 1.5rem; color: #334155; }}
        .topbar {{ background: #0f172a; color: #f8fafc; padding: 1rem 1.5rem; margin: -1.5rem -1.5rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }}
        .topbar h1 {{ font-size: 1.25rem; }}
        .topbar a {{ color: #94a3b8; text-decoration: none; }}
        a {{ color: #0f172a; font-weight: 500; }}
    </style>
</head>
<body>
    <header class="topbar"><h1>AskOGMS</h1><a href="/">Chat</a></header>
    <p>Error: {str(e)}</p>
    <a href="/">Back to chat</a>
</body>
</html>""", 500

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
