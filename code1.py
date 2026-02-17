from untitled0 import chain_code
from langchain_community.chat_message_histories import ChatMessageHistory
from flask import Flask, request, jsonify, render_template_string, render_template
from flask_cors import CORS  # Import CORS
import sqlite3
import os
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app) 

# Create an instance of ChatMessageHistory to store conversation
history = ChatMessageHistory()

# Main UI route
@app.route('/')
def index():
    return render_template_string("""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskDB - Natural Language Database Query</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 1200px;
            height: 80vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .main-content {
            flex: 1;
            display: flex;
            flex-direction: column;
            padding: 30px;
        }
        
        .chat-container {
            flex: 1;
            display: flex;
            flex-direction: column;
            border: 2px solid #e1e5e9;
            border-radius: 15px;
            overflow: hidden;
            margin-bottom: 20px;
        }
        
        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
            max-height: 400px;
        }
        
        .message {
            margin-bottom: 15px;
            padding: 15px 20px;
            border-radius: 15px;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .user-message {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            margin-left: auto;
            border-bottom-right-radius: 5px;
        }
        
        .bot-message {
            background: white;
            border: 1px solid #e1e5e9;
            margin-right: auto;
            border-bottom-left-radius: 5px;
        }
        
        .input-container {
            display: flex;
            padding: 20px;
            background: white;
            border-top: 1px solid #e1e5e9;
        }
        
        .input-container input {
            flex: 1;
            padding: 15px 20px;
            border: 2px solid #e1e5e9;
            border-radius: 25px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s;
        }
        
        .input-container input:focus {
            border-color: #667eea;
        }
        
        .input-container button {
            margin-left: 15px;
            padding: 15px 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s;
        }
        
        .input-container button:hover {
            transform: translateY(-2px);
        }
        
        .input-container button:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .loading.show {
            display: block;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .quick-actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .quick-action {
            padding: 15px 20px;
            background: #f8f9fa;
            border: 2px solid #e1e5e9;
            border-radius: 10px;
            cursor: pointer;
            text-align: center;
            transition: all 0.3s;
            font-size: 14px;
        }
        
        .quick-action:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .nav-buttons {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 20px;
        }
        
        .nav-button {
            padding: 12px 25px;
            background: #f8f9fa;
            border: 2px solid #e1e5e9;
            border-radius: 25px;
            text-decoration: none;
            color: #333;
            transition: all 0.3s;
            font-size: 14px;
        }
        
        .nav-button:hover {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }
        
        .welcome-message {
            text-align: center;
            color: #666;
            font-style: italic;
            margin: 20px 0;
        }
        
        @media (max-width: 768px) {
            .container {
                height: 90vh;
                margin: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .main-content {
                padding: 20px;
            }
            
            .quick-actions {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🗄️ AskDB</h1>
            <p>Ask questions about your database in natural language</p>
        </div>
        
        <div class="main-content">
            <div class="quick-actions">
                <div class="quick-action" onclick="askQuestion('How many contacts are there?')">
                    📊 Total Contacts
                </div>
                <div class="quick-action" onclick="askQuestion('What programs are available?')">
                    🎓 Available Programs
                </div>
                <div class="quick-action" onclick="askQuestion('Show me all pending payments')">
                    💳 Pending Payments
                </div>
                <div class="quick-action" onclick="askQuestion('Which students are enrolled in Data Science?')">
                    👥 Data Science Students
                </div>
                <div class="quick-action" onclick="askQuestion('What is the total revenue?')">
                    💰 Total Revenue
                </div>
                <div class="quick-action" onclick="askQuestion('Show me all open support cases')">
                    🎫 Open Cases
                </div>
            </div>
            
            <div class="chat-container">
                <div class="chat-messages" id="chatMessages">
                    <div class="welcome-message">
                        👋 Welcome! Ask me anything about your database. Try clicking one of the quick actions above or type your own question.
                    </div>
                </div>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <div>Thinking...</div>
                </div>
                
                <div class="input-container">
                    <input type="text" id="questionInput" placeholder="Ask a question about your database..." onkeypress="handleKeyPress(event)">
                    <button onclick="askQuestion()" id="askButton">Ask</button>
                </div>
            </div>
            
            <div class="nav-buttons">
                <a href="/view-data" class="nav-button" target="_blank">📋 View Database</a>
                <a href="/api" class="nav-button" target="_blank">🔗 API Endpoint</a>
                <button class="nav-button" onclick="clearChat()">🗑️ Clear Chat</button>
            </div>
        </div>
    </div>

    <script>
        function askQuestion(question = null) {
            const input = document.getElementById('questionInput');
            const questionText = question || input.value.trim();
            
            if (!questionText) return;
            
            // Clear input if using text box
            if (!question) {
                input.value = '';
            }
            
            // Add user message
            addMessage(questionText, 'user');
            
            // Show loading
            showLoading(true);
            
            // Disable button
            document.getElementById('askButton').disabled = true;
            
            // Send request
            fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: questionText })
            })
            .then(response => response.json())
            .then(data => {
                showLoading(false);
                if (data.answer !== undefined && data.answer !== null) {
                    const a = data.answer;
                    const text = typeof a === 'string' ? a : (a?.text || a?.content || JSON.stringify(a));
                    addMessage(text, 'bot');
                } else if (data.error) {
                    addMessage('Error: ' + data.error, 'bot');
                }
            })
            .catch(error => {
                showLoading(false);
                addMessage('Error: ' + error.message, 'bot');
            })
            .finally(() => {
                document.getElementById('askButton').disabled = false;
            });
        }
        
        function addMessage(text, type) {
            const messagesContainer = document.getElementById('chatMessages');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;
            messageDiv.textContent = text;
            
            // Remove welcome message if it exists
            const welcomeMessage = messagesContainer.querySelector('.welcome-message');
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function showLoading(show) {
            const loading = document.getElementById('loading');
            if (show) {
                loading.classList.add('show');
            } else {
                loading.classList.remove('show');
            }
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                askQuestion();
            }
        }
        
        function clearChat() {
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = '<div class="welcome-message">👋 Welcome! Ask me anything about your database. Try clicking one of the quick actions above or type your own question.</div>';
        }
        
        // Focus on input when page loads
        window.onload = function() {
            document.getElementById('questionInput').focus();
        };
    </script>
</body>
</html>
    """)

# Create an instance of ChatMessageHistory to store conversation
history = ChatMessageHistory()

# API endpoint to handle chat messages
@app.route('/api', methods=['POST'])
def master1():
    try:
        # Parse the JSON body to get the user's question
        data = request.get_json()
        q = data.get('question')  # Get 'q' from the API request body
        
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

        # Ensure answer is always a string (extract from LLM dict shape if needed)
        if isinstance(res, str):
            answer_text = res
        elif isinstance(res, dict):
            answer_text = res.get("text") or res.get("content")
            if not isinstance(answer_text, str):
                answer_text = str(answer_text) if answer_text is not None else str(res)
        else:
            answer_text = str(res) if res is not None else "No response generated."

        # Add AI response to history
        history.add_ai_message(answer_text)

        # Return the AI response as JSON
        return jsonify({"answer": answer_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Database viewer endpoint
@app.route('/view-data')
def view_data():
    try:
        # Check database type from environment
        import os
        from dotenv import load_dotenv
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
            # SQLite fallback (when DB_TYPE=sqlite)
            conn = sqlite3.connect(os.getenv("DB_NAME", "askdb_local.db"))
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
        
        # HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AskDB Database Viewer</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; }
                h1 { color: #333; text-align: center; }
                .table-section { background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
                th { background-color: #3498db; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                tr:hover { background-color: #e8f4fd; }
                .stats { background: #e8f5e8; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
                .nav { text-align: center; margin: 20px 0; }
                .nav a { margin: 0 10px; padding: 10px 20px; background: #3498db; color: white; text-decoration: none; border-radius: 5px; }
                .nav a:hover { background: #2980b9; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🗄️ AskDB Database Viewer</h1>
                
                <div class="stats">
                    <h3>📊 Database Overview</h3>
                    <p><strong>Total Tables:</strong> {{ tables|length }}</p>
                    <p><strong>Total Records:</strong> {{ total_records }}</p>
                </div>
                
                <div class="nav">
                    <a href="/view-data">🔄 Refresh</a>
                    <a href="/api" target="_blank">🤖 Ask Questions</a>
                </div>
                
                {% for table_name, data in table_data.items() %}
                <div class="table-section">
                    <h2>📋 {{ table_name.upper() }} ({{ data.rows|length }} records)</h2>
                    <table>
                        <thead>
                            <tr>
                                {% for column in data.columns %}
                                <th>{{ column }}</th>
                                {% endfor %}
                            </tr>
                        </thead>
                        <tbody>
                            {% for row in data.rows %}
                            <tr>
                                {% for cell in row %}
                                <td>{{ cell if cell is not none else '' }}</td>
                                {% endfor %}
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
                {% endfor %}
            </div>
        </body>
        </html>
        """
        
        # Calculate total records
        total_records = sum(len(data['rows']) for data in table_data.values())
        
        return render_template_string(html_template, 
                                    table_data=table_data, 
                                    tables=tables,
                                    total_records=total_records)
        
    except Exception as e:
        return f"Error: {str(e)}", 500

# Simple table viewer endpoint
@app.route('/table/<table_name>')
def view_table(table_name):
    try:
        conn = sqlite3.connect('askdb_local.db')
        cursor = conn.cursor()
        
        # Get column names
        cursor.execute(f'PRAGMA table_info({table_name})')
        columns = [col[1] for col in cursor.fetchall()]
        
        # Get all data
        cursor.execute(f'SELECT * FROM {table_name}')
        rows = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            "table": table_name,
            "columns": columns,
            "data": rows,
            "count": len(rows)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
