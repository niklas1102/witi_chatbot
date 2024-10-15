from flask import Flask, request, jsonify, render_template, session
import openai
from flask_session import Session

app = Flask(__name__, static_folder="static", template_folder="static")

# Replace this with your actual OpenAI API key
openai.api_key = 'API_KEY'
app.config['SESSION_TYPE'] = 'filesystem'  # Use filesystem to store session data
app.config['SECRET_KEY'] = 'supersecretkey'  # Change this to a secure random key in production
Session(app)  # Initialize the session extension

# Load specific knowledge from a .txt file
def load_knowledge(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            knowledge = file.read()
        return knowledge
    except Exception as e:
        print(f"Error loading knowledge file: {e}")
        return ""

# Path to your knowledge base .txt file
KNOWLEDGE_FILE = 'knowledge.txt'  # Ensure this file exists in your project directory

# Load knowledge once when the app starts
specific_knowledge = load_knowledge(KNOWLEDGE_FILE)

@app.route('/')
def index():
    """
    Serve the main page and reset chat history on page load.
    """
    # Clear the session completely when the page loads (ensures no session persistence)
    session.clear()
    return render_template('index.html')

def ask_chatbot(question):
    """
    Send the user's question along with the chat history and specific knowledge to OpenAI's API and return the response.
    """
    # Retrieve the chat history from the session
    history = session.get('history', [])
    
    # Prepare the messages for the ChatCompletion API
    messages = [
        {"role": "system", "content": "You are a helpful assistant specialized in assisting users with information from this website."},
        {"role": "system", "content": f"Here is some information you should know: {specific_knowledge}"}
    ]
    messages += history  # Add previous conversation to maintain context
    messages.append({"role": "user", "content": question})  # Add the current user question
    
    try:
        # Call the OpenAI ChatCompletion API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        bot_response = response['choices'][0]['message']['content'].strip()
        
        # Update the session history with the latest user and bot messages
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": bot_response})
        session['history'] = history  # Reassign to ensure session detects the change
        
        return bot_response
    except Exception as e:
        return f"Error: {e}"

@app.route('/chat', methods=['POST'])
def chat():
    """
    Handle chat requests from the frontend.
    """
    user_question = request.form.get('question')
    if not user_question:
        return jsonify("Please enter a question."), 400
    chatbot_response = ask_chatbot(user_question)
    return jsonify(chatbot_response)

@app.route('/reset', methods=['POST'])
def reset_chat():
    """
    Reset the chat history (optional manual reset).
    """
    session.clear()  # Completely clear the session to reset everything
    return jsonify("Chat history has been reset.")

if __name__ == '__main__':
    app.run(debug=True)
