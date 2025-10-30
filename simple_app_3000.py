from untitled0 import chain_code
from langchain_community.chat_message_histories import ChatMessageHistory
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app) 

# Create an instance of ChatMessageHistory to store conversation
history = ChatMessageHistory()

# Simple test route
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>AskDB - Test</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f0f0f0; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; text-align: center; }
            .input-group { margin: 20px 0; }
            input { width: 70%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            .response { margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗄️ AskDB - Database Query Interface</h1>
            <p>Ask questions about your database in natural language</p>
            
            <div class="input-group">
                <input type="text" id="question" placeholder="Ask a question about your database..." />
                <button onclick="askQuestion()">Ask</button>
            </div>
            
            <div id="response" class="response" style="display: none;"></div>
            
            <div style="margin-top: 30px; text-align: center;">
                <a href="/view-data" style="margin: 0 10px; padding: 10px 20px; background: #28a745; color: white; text-decoration: none; border-radius: 5px;">📋 View Database</a>
                <a href="/api" style="margin: 0 10px; padding: 10px 20px; background: #17a2b8; color: white; text-decoration: none; border-radius: 5px;">🔗 API</a>
            </div>
        </div>
        
        <script>
            function askQuestion() {
                const question = document.getElementById('question').value;
                if (!question.trim()) return;
                
                const responseDiv = document.getElementById('response');
                responseDiv.style.display = 'block';
                responseDiv.innerHTML = 'Loading...';
                
                fetch('/api', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.answer) {
                        responseDiv.innerHTML = '<strong>Answer:</strong><br>' + data.answer;
                    } else if (data.error) {
                        responseDiv.innerHTML = '<strong>Error:</strong><br>' + data.error;
                    }
                })
                .catch(error => {
                    responseDiv.innerHTML = '<strong>Error:</strong><br>' + error.message;
                });
            }
            
            // Allow Enter key
            document.getElementById('question').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    askQuestion();
                }
            });
        </script>
    </body>
    </html>
    '''

# API endpoint to handle chat messages
@app.route('/api', methods=['POST'])
def master1():
    try:
        # Parse the JSON body to get the user's question
        data = request.get_json()
        q = data.get('question')  # Get 'question' from the API request body
        
        if not q:
            return jsonify({"error": "Missing 'question' in the request body"}), 400

        # Add user message to history
        history.add_user_message(q)

        # Prepare the messages in the format expected by chain_code
        formatted_messages = [
            {"role": "user" if msg.type == "user" else "assistant", "content": msg.content}
            for msg in history.messages
        ]

        # Generate AI response using the chain_code function
        res = chain_code(q, formatted_messages)

        # Add AI response to history
        history.add_ai_message(res)

        # Return the AI response as JSON
        return jsonify({"answer": res})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Database viewer endpoint
@app.route('/view-data')
def view_data():
    try:
        # Check database type from environment
        load_dotenv()
        db_type = os.getenv("DB_TYPE", "sqlite")
        
        if db_type.lower() == "postgresql":
            import psycopg2
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST", "localhost"),
                port=os.getenv("DB_PORT", "5432"),
                user=os.getenv("DB_USER", "postgres"),
                password=os.getenv("DB_PASSWORD", ""),
                database=os.getenv("DB_NAME", "askdb")
            )
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Get data from each table
            table_data = {}
            for table in tables:
                cursor.execute(f'SELECT * FROM {table}')
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}'")
                columns = [col[0] for col in cursor.fetchall()]
                
                table_data[table] = {
                    'columns': columns,
                    'rows': rows
                }
            
            conn.close()
        else:
            # SQLite fallback
            conn = sqlite3.connect('askdb_local.db')
            cursor = conn.cursor()
            
            # Get all table names
            cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name NOT LIKE "sqlite_%"')
            tables = [table[0] for table in cursor.fetchall()]
            
            # Get data from each table
            table_data = {}
            for table in tables:
                cursor.execute(f'SELECT * FROM {table}')
                rows = cursor.fetchall()
                
                # Get column names
                cursor.execute(f'PRAGMA table_info({table})')
                columns = [col[1] for col in cursor.fetchall()]
                
                table_data[table] = {
                    'columns': columns,
                    'rows': rows
                }
            
            conn.close()
        
        # Simple HTML template
        html = "<h1>Database Viewer</h1>"
        for table_name, data in table_data.items():
            html += f"<h2>{table_name}</h2>"
            html += "<table border='1'><tr>"
            for col in data['columns']:
                html += f"<th>{col}</th>"
            html += "</tr>"
            for row in data['rows']:
                html += "<tr>"
                for cell in row:
                    html += f"<td>{cell if cell is not none else ''}</td>"
                html += "</tr>"
            html += "</table><br>"
        
        return html
        
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    app.run(debug=True, port=3000)
