import os, sys, json, datetime, uuid
from flask import Flask, request, jsonify, render_template, url_for, redirect, flash, session
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
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
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],
    storage_uri="memory://",
)

app.secret_key = os.environ["APP_SECRET_KEY"]

histories = {}
locked = False

class Logger:
    '''## Intro
    A class offering silent and quick logging services.

    Explicit permission must be granted by setting `LoggingEnabled` to `True` in the `.env` file. Otherwise, all logging services will be disabled.
    
    ## Usage:
    ```
    Logger.setup() ## Optional

    Logger.log("Hello world!") ## Adds a log entry to the logs.txt database file, if permission was granted.
    ```
    '''
    
    @staticmethod
    def checkPermission():
        if "LoggingEnabled" in os.environ and os.environ["LoggingEnabled"] == 'True':
            return True
        else:
            return False

    @staticmethod
    def setup():
        if Logger.checkPermission():
            try:
                if not os.path.exists(os.path.join(os.getcwd(), "logs.txt")):
                    with open("logs.txt", "w") as f:
                        f.write("{}UTC {}\n".format(datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"), "LOGGER: Logger database file setup complete."))
            except Exception as e:
                print("LOGGER SETUP ERROR: Failed to setup logs.txt database file. Setup permissions have been granted. Error: {}".format(e))

        return

    @staticmethod
    def log(message, debugPrintExplicitDeny=False):
        if "DebugMode" in os.environ and os.environ["DebugMode"] == 'True' and (not debugPrintExplicitDeny):
            print("LOG: {}".format(message))
        if Logger.checkPermission():
            try:
                with open("logs.txt", "a") as f:
                    f.write("{}UTC {}\n".format(datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M:%S"), message))
            except Exception as e:
                print("LOGGER LOG ERROR: Failed to log message. Error: {}".format(e))
        
        return
    
    @staticmethod
    def destroyAll():
        try:
            if os.path.exists(os.path.join(os.getcwd(), "logs.txt")):
                os.remove("logs.txt")
        except Exception as e:
            print("LOGGER DESTROYALL ERROR: Failed to destroy logs.txt database file. Error: {}".format(e))

    @staticmethod
    def readAll():
        if not Logger.checkPermission():
            return "ERROR: Logging-related services do not have permission to operate."
        try:
            if os.path.exists(os.path.join(os.getcwd(), "logs.txt")):
                with open("logs.txt", "r") as f:
                    logs = f.readlines()
                    for logIndex in range(len(logs)):
                        logs[logIndex] = logs[logIndex].replace("\n", "")
                    return logs
            else:
                return []
        except Exception as e:
            print("LOGGER READALL ERROR: Failed to check and read logs.txt database file. Error: {}".format(e))
            return "ERROR: Failed to check and read logs.txt database file. Error: {}".format(e)

class Gemini:
    model = genai.GenerativeModel('gemini-pro')
    chat = model.start_chat(history=[])

    @staticmethod
    def sendMessage(msg, historyInstanceID=None):
        try:
            response = Gemini.chat.send_message(msg)
            Logger.log("GEMINI: Sent chat message in instance '{}': '{}'".format("ID Not Available" if historyInstanceID == None else historyInstanceID, msg))
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

@app.before_request
def beforeRequest():
    if locked and (not request.path.startswith("/debug")):
        return "<h1>GeminiBot is currently unavailable. Please try again later.</h1>"

@app.route('/', methods=['GET'])
def homepage():
    global histories

    if 'instanceID' not in session or session['instanceID'] not in histories:
        session['instanceID'] = str(uuid.uuid4().hex)
        histories[session['instanceID']] = []
    
    return render_template('index.html', chat=processHistory(histories.get(session['instanceID'], [])), instanceID=session['instanceID'])
    
@app.route('/sendChatMessage', methods=['POST'])
@limiter.limit("15/minute")
def sendChatMessage():
    global histories

    if 'instanceID' not in session or session['instanceID'] not in histories:
        session['instanceID'] = str(uuid.uuid4().hex)
        histories[session['instanceID']] = []

    if 'message' not in request.form or request.form['message'].strip() == "":
        flash("Please enter a message.")
        return redirect(url_for('homepage'))
        
    message = request.form['message']

    Gemini.chat.history = histories.get(session['instanceID'], [])
    response = Gemini.sendMessage(message, historyInstanceID=session['instanceID'])

    if response.startswith("ERROR:"):
        Gemini.clearChatHistory()
        flash(response)
        return redirect(url_for('homepage'))
        
    histories[session['instanceID']] = Gemini.getChatHistory()
    Gemini.clearChatHistory()
        
    return redirect(url_for('homepage'))
    
@app.route('/clear')
def clearChat():
    global histories

    if 'instanceID' in session and session['instanceID'] in histories:
        del histories[session['instanceID']]
    session.clear()
    return redirect(url_for('homepage'))

@app.route('/debug/<accessKey>')
def debug(accessKey):
    if accessKey != os.environ["APP_SECRET_KEY"]:
        return "ERROR: Access denied."
    
    return """
<h1>Options:</h1>
<ul>
<li>View Logs: /debug/ACCESS_KEY/logs</li>
<li>Toggle Lock: /debug/ACCESS_KEY/toggleLock</li>
<li>Clear Histories: /debug/ACCESS_KEY/clearHistories</li>
</ul>
"""

@app.route('/debug/<accessKey>/logs')
def debugLogs(accessKey):
    if accessKey != os.environ["APP_SECRET_KEY"]:
        return "ERROR: Access denied."
    
    return "<br>".join(Logger.readAll())

@app.route('/debug/<accessKey>/toggleLock')
def debugLock(accessKey):
    global locked

    if accessKey != os.environ["APP_SECRET_KEY"]:
        return "ERROR: Access denied."
    
    locked = not locked
    Logger.log("DEBUG: Toggled lock status to '{}'.".format("Locked" if locked else "Unlocked"))
    return "SUCCESS: {}.".format("Locked" if locked else "Unlocked")

@app.route('/debug/<accessKey>/clearHistories')
def debugClearHistories(accessKey):
    global histories

    if accessKey != os.environ["APP_SECRET_KEY"]:
        return "ERROR: Access denied."
    
    histories = {}
    Logger.log("DEBUG: Cleared all chat histories.")
    return "SUCCESS: Cleared all chat histories."

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)