import os, sys, json
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash
from flask_cors import CORS
import google.generativeai as genai
from dotenv import load_dotenv
load_dotenv()

try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except Exception as e:
    print("Unable to configure Gemini: {}".format(e))
    sys.exit(1)

app = Flask(__name__)
CORS(app)

app.secret_key = "myGeminiApp"

class Gemini:
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])

    @staticmethod
    def sendMessage(msg):
        try:
            response = Gemini.chat.send_message(msg)
            return response.text
        except Exception as e:
            return "ERROR: Failed to send chat message; error: {}".format(e)
        
    @staticmethod
    def getChatHistory():
        return Gemini.chat.history
    
    @staticmethod
    def clearChatHistory():
        Gemini.chat.history = []
        return True

def processHistory(history) -> list:
    output = []
    for item in reversed(history):
        output.append({
            "role": "You" if item.role == "user" else "GeminiBot",
            "message": item.parts[0].text
        })

    return output

@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'GET':
        return render_template('index.html', chat=processHistory(Gemini.getChatHistory()))
    else:
        if 'message' not in request.form or request.form['message'].strip() == "":
            flash("Please enter a message.")
            return redirect(url_for('homepage'))
        
        message = request.form['message']
        response = Gemini.sendMessage(message)
        if response.startswith("ERROR:"):
            flash(response)
            return redirect(url_for('homepage'))
        
        return redirect(url_for('homepage'))
    
@app.route('/clear')
def clearChat():
    Gemini.clearChatHistory()
    return redirect(url_for('homepage'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)