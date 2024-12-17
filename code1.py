from untitled0 import chain_code
from langchain_community.chat_message_histories import ChatMessageHistory
from flask import Flask, request, jsonify
from flask_cors import CORS  # Import CORS

app = Flask(__name__)
CORS(app) 

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
            return jsonify({"error": "Missing 'q' in the request body"}), 400

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

if __name__ == '__main__':
    app.run(debug=True)
