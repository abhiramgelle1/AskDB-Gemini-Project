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

# ChatGPT-style UI route
@app.route('/')
def index():
    return render_template_string(r"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AskDB - AI Database Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: #343541;
            color: #ffffff;
            height: 100vh;
            overflow: hidden;
        }
        
        .chat-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        
        .header {
            background: #202123;
            padding: 1rem 1.5rem;
            border-bottom: 1px solid #4d4d4f;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header h1 {
            font-size: 1.25rem;
            font-weight: 600;
            color: #ffffff;
        }
        
        .header-actions {
            display: flex;
            gap: 0.5rem;
        }
        
        .btn {
            padding: 0.5rem 1rem;
            border: 1px solid #4d4d4f;
            background: transparent;
            color: #ffffff;
            border-radius: 0.375rem;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        
        .btn:hover {
            background: #4d4d4f;
        }
        
        .btn-primary {
            background: #10a37f;
            border-color: #10a37f;
        }
        
        .btn-primary:hover {
            background: #0d8a6b;
        }
        
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            gap: 1rem;
        }
        
        .message {
            display: flex;
            gap: 0.75rem;
            max-width: 100%;
        }
        
        .message.user {
            flex-direction: row-reverse;
        }
        
        .message-avatar {
            width: 2rem;
            height: 2rem;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 0.875rem;
            flex-shrink: 0;
        }
        
        .message.user .message-avatar {
            background: #10a37f;
        }
        
        .message.assistant .message-avatar {
            background: #444654;
        }
        
        .message-content {
            background: #444654;
            padding: 1rem;
            border-radius: 0.75rem;
            max-width: 80%;
            word-wrap: break-word;
        }
        
        .message.user .message-content {
            background: #10a37f;
        }
        
        .message-text {
            line-height: 1.5;
        }
        
        .message-text pre {
            background: rgba(0, 0, 0, 0.2);
            padding: 0.75rem;
            border-radius: 0.5rem;
            overflow-x: auto;
            margin: 0.5rem 0;
        }
        
        .message-text code {
            background: rgba(0, 0, 0, 0.2);
            padding: 0.125rem 0.25rem;
            border-radius: 0.25rem;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }
        
        .message-text strong {
            font-weight: 600;
            color: #10a37f;
        }
        
        .message-text em {
            font-style: italic;
            opacity: 0.9;
        }
        
        .message-text ul,
        .message-text ol {
            margin: 0.5rem 0;
            padding-left: 1.5rem;
        }
        
        .message-text li {
            margin: 0.25rem 0;
            line-height: 1.6;
        }
        
        .welcome-message {
            text-align: center;
            padding: 2rem;
            color: #8e8ea0;
        }
        
        .welcome-title {
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #ffffff;
        }
        
        .welcome-subtitle {
            font-size: 1rem;
            margin-bottom: 2rem;
        }
        
        .quick-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            justify-content: center;
        }
        
        .quick-action {
            background: #444654;
            border: 1px solid #4d4d4f;
            color: #ffffff;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            cursor: pointer;
            font-size: 0.875rem;
            transition: all 0.2s;
        }
        
        .quick-action:hover {
            background: #4d4d4f;
        }
        
        .input-container {
            background: #202123;
            padding: 1rem 1.5rem;
            border-top: 1px solid #4d4d4f;
            display: flex;
            gap: 0.75rem;
            align-items: flex-end;
        }
        
        .input-wrapper {
            flex: 1;
            position: relative;
        }
        
        .question-input {
            width: 100%;
            background: #40414f;
            border: 1px solid #4d4d4f;
            color: #ffffff;
            padding: 0.75rem 1rem;
            border-radius: 0.5rem;
            font-size: 1rem;
            resize: none;
            min-height: 2.5rem;
            max-height: 8rem;
            font-family: inherit;
        }
        
        .question-input:focus {
            outline: none;
            border-color: #10a37f;
        }
        
        .question-input::placeholder {
            color: #8e8ea0;
        }
        
        .send-button {
            background: #10a37f;
            border: none;
            color: #ffffff;
            padding: 0.75rem;
            border-radius: 0.5rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.2s;
            min-width: 2.5rem;
        }
        
        .send-button:hover {
            background: #0d8a6b;
        }
        
        .send-button:disabled {
            background: #4d4d4f;
            cursor: not-allowed;
        }
        
        .loading {
            display: none;
            align-items: center;
            gap: 0.5rem;
            color: #8e8ea0;
            font-size: 0.875rem;
        }
        
        .loading.show {
            display: flex;
        }
        
        .typing-indicator {
            display: flex;
            gap: 0.25rem;
        }
        
        .typing-dot {
            width: 0.375rem;
            height: 0.375rem;
            background: #8e8ea0;
            border-radius: 50%;
            animation: typing 1.4s infinite ease-in-out;
        }
        
        .typing-dot:nth-child(1) { animation-delay: -0.32s; }
        .typing-dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes typing {
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }
        
        @media (max-width: 768px) {
            .header {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 1rem;
            }
            
            .chat-messages {
                padding: 0.75rem;
            }
            
            .message-content {
                max-width: 90%;
            }
            
            .input-container {
                padding: 1rem;
            }
            
            .quick-actions {
                flex-direction: column;
                align-items: center;
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="header">
            <h1>🗄️ AskDB - AI Database Assistant</h1>
            <div class="header-actions">
                <button class="btn" onclick="clearChat()">🗑️ Clear</button>
            </div>
        </div>
        
        <div class="chat-messages" id="chatMessages">
            <div class="welcome-message">
                <div class="welcome-title">Welcome to AskDB</div>
                <div class="welcome-subtitle">Ask questions about your database in natural language</div>
                
                <div class="quick-actions">
                    <div class="quick-action" onclick="askQuestion('How many contacts are there?')">
                        How many contacts are there?
                    </div>
                    <div class="quick-action" onclick="askQuestion('Show me all customers from California')">
                        Show me all customers from California
                    </div>
                    <div class="quick-action" onclick="askQuestion('What are the top 5 products by sales?')">
                        What are the top 5 products by sales?
                    </div>
                    <div class="quick-action" onclick="askQuestion('List all pending cases')">
                        List all pending cases
                    </div>
                </div>
            </div>
        </div>
        
        <div class="input-container">
            <div class="input-wrapper">
                <textarea 
                    id="questionInput" 
                    class="question-input" 
                    placeholder="Ask a question about your database..."
                    rows="1"
                ></textarea>
            </div>
            <button id="sendButton" class="send-button" onclick="sendMessage()">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"/>
                </svg>
            </button>
        </div>
        
        <div class="loading" id="loadingIndicator">
            <span>AskDB is thinking</span>
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    </div>

    <script>
        let isLoading = false;
        
        function askQuestion(question) {
            document.getElementById('questionInput').value = question;
            sendMessage();
        }
        
        function sendMessage() {
            console.log('sendMessage called');
            const input = document.getElementById('questionInput');
            const question = input.value.trim();
            
            console.log('Question:', question);
            console.log('isLoading:', isLoading);
            
            if (!question || isLoading) {
                console.log('Returning early - no question or already loading');
                return;
            }
            
            // Add user message
            addMessage(question, 'user');
            
            // Clear input
            input.value = '';
            input.style.height = 'auto';
            
            // Show loading
            setLoading(true);
            
            console.log('Sending to API...');
            // Send to API
            fetch('/api', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question })
            })
            .then(response => {
                console.log('Response received:', response);
                return response.json();
            })
            .then(data => {
                console.log('Data:', data);
                setLoading(false);
                
                if (data.error) {
                    addMessage('Sorry, I encountered an error: ' + data.error, 'assistant');
                } else {
                    addMessage(data.answer, 'assistant');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                setLoading(false);
                addMessage('Sorry, I encountered an error: ' + error.message, 'assistant');
            });
        }
        
        function addMessage(text, sender) {
            const messagesContainer = document.getElementById('chatMessages');
            const welcomeMessage = messagesContainer.querySelector('.welcome-message');
            
            // Remove welcome message if it exists
            if (welcomeMessage) {
                welcomeMessage.remove();
            }
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}`;
            
            const avatar = sender === 'user' ? '👤' : '🤖';
            
            messageDiv.innerHTML = `
                <div class="message-avatar">${avatar}</div>
                <div class="message-content">
                    <div class="message-text">${formatMessage(text)}</div>
                </div>
            `;
            
            messagesContainer.appendChild(messageDiv);
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }
        
        function formatMessage(text) {
            // Convert SQL queries to code blocks
            text = text.replace(/```sql\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
            text = text.replace(/```\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
            
            // Convert bold text **text** to <strong>
            text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            
            // Convert italic text *text* to <em>
            text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
            
            // Convert inline code
            text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
            
            // Convert bullet points
            text = text.replace(/^\* (.+)$/gm, '<li>$1</li>');
            text = text.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
            
            // Convert numbered lists
            text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
            
            // Convert line breaks
            text = text.replace(/\n/g, '<br>');
            
            return text;
        }
        
        function setLoading(loading) {
            isLoading = loading;
            const loadingIndicator = document.getElementById('loadingIndicator');
            const sendButton = document.getElementById('sendButton');
            
            if (loading) {
                loadingIndicator.classList.add('show');
                sendButton.disabled = true;
            } else {
                loadingIndicator.classList.remove('show');
                sendButton.disabled = false;
            }
        }
        
        function clearChat() {
            const messagesContainer = document.getElementById('chatMessages');
            messagesContainer.innerHTML = `
                <div class="welcome-message">
                    <div class="welcome-title">Welcome to AskDB</div>
                    <div class="welcome-subtitle">Ask questions about your database in natural language</div>
                    
                    <div class="quick-actions">
                        <div class="quick-action" onclick="askQuestion('How many contacts are there?')">
                            How many contacts are there?
                        </div>
                        <div class="quick-action" onclick="askQuestion('Show me all customers from California')">
                            Show me all customers from California
                        </div>
                        <div class="quick-action" onclick="askQuestion('What are the top 5 products by sales?')">
                            What are the top 5 products by sales?
                        </div>
                        <div class="quick-action" onclick="askQuestion('List all pending cases')">
                            List all pending cases
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Auto-resize textarea
        document.getElementById('questionInput').addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = Math.min(this.scrollHeight, 8 * 16) + 'px';
        });
        
        // Send message on Enter (but allow Shift+Enter for new lines)
        document.getElementById('questionInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Focus input on load
        window.onload = function() {
            document.getElementById('questionInput').focus();
        };
    </script>
</body>
</html>
    """)

# API endpoint to handle chat messages
@app.route('/api', methods=['POST'])
def master1():
    try:
        data = request.get_json()
        question = data.get('question', '')
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        # Use the chain_code function from untitled0.py
        res = chain_code(question)
        
        return jsonify({"answer": res})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=2002)