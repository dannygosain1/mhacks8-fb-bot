import os
import sys
import json
import requests
import simplejson
from flask import Flask, request
from flask_pymongo import PyMongo
# from bson import ObjectId
# from bson import json_util
# from bson.json_util import dumps
# import ast

# Create Flask App
app = Flask(__name__)

# Set Up Database Connections
app.config['MONGO_DBNAME'] = 'portfolio-risk-bot'
app.config['MONGO_URI'] = 'mongodb://mhacks8:mhacks8@ds053216.mlab.com:53216/portfolio-risk-bot'

# Create Database Object
mongo = PyMongo(app)

# Send help message to user
def send_help_message(sender_id):
    help_message = ("Usage: [option] ... [argument] ... [params]\n"
                    "Options and arguments:\n\n"  
                    "portfolio [show]: display contents of exisiting protfolio\n" 
                    "portfolio [buy | sell] (security, quantity): update exisiting protfolio\n" 
                    "analysis [ | ]: analyze portfolio risk"
                    "help: show this menu"))
    send_message(sender_id, help_message)

# Send greeting message to user
def send_greeting_message(sender_id):
    greeting_message = "Hi, I'm RiskBot! How can I help you today? Enter a suitable option or [help] to view the help menu..."
    send_message(sender_id, greeting_message)

@app.route('/')
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.route('/test', methods=['GET'])
def test():
    mongo.db.portfolio.insert({ "name": "sadu" })
    return "Hello world test", 200

@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    data = request.get_json()
    log(data)

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message



                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = str(messaging_event["message"]["text"]).upper()  # the message's text

                    if message_text == "ANALYSIS":
                        pass
                    elif message_text == "PORTFOLIO":
                        pass
                    elif message_text == "HELP":
                        send_help_message(sender_id)
                    else:
                        send_greeting_message(sender_id)


                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
