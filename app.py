import os
import sys
import json
import requests
import blackrock
import traceback
import simplejson
from flask import Flask, request
from flask_pymongo import PyMongo
from bson.json_util import dumps

# Create Flask App
app = Flask(__name__)

# Set Up Database Connections
app.config['MONGO_DBNAME'] = 'portfolio-risk-bot'
app.config['MONGO_URI'] = 'mongodb://mhacks8:mhacks8@ds053216.mlab.com:53216/portfolio-risk-bot'

# Create Database Object
mongo = PyMongo(app)

# LUIS Params
base_luis_url = "https://api.projectoxford.ai/luis/v1/application?id=307094a8-2412-411c-ab55-a431c9b2dd0c&subscription-key=280d1db7507743198e85cdedcb8c94ce&q="

# Build LUIS URL
def build_luis_url(base_url, app_id, subscription_key, query):
    return (base_url + "id=%s" + "&subscription-key=%s" + "&q=%s") % (app_id, subscription_key, query)

# Get Response from the Microsoft LUIS API
def get_response_from_luis_api(query):
    base_url = "https://api.projectoxford.ai/luis/v1/application?"
    app_id = "307094a8-2412-411c-ab55-a431c9b2dd0c"
    subscription_key = "280d1db7507743198e85cdedcb8c94ce"
    log(build_luis_url(base_url, app_id, subscription_key, query))
    r = json.loads(requests.get(build_luis_url(base_url, app_id, subscription_key, query)).text)
    log(r)
    return r


# Send help message to user
def send_help_message(sender_id):
    help_message = ("Usage: [option] ... [argument] ... [params]\n\n"
                    "Options and arguments:\n"  
                    "portfolio [show]: display contents of exisiting protfolio\n" 
                    "portfolio [buy|sell] [ticker] [qty]: update exisiting protfolio\n" 
                    "analysis [scenario]: analyze portfolio risk\n"
                    "help: show this menu")
    get_response_from_luis_api("hello")
    send_message(sender_id, help_message)

# Send greeting message to user
def send_greeting_message(sender_id):
    greeting_message = "Hi, I'm Risk-Bot! How can I help you today?"
    # "Enter a suitable option or [help] to view the help menu...")
    send_message(sender_id, greeting_message)

# Send existing portfolio to user
def send_portfolio(sender_id):
    portfolio = mongo.db.portfolio.find( {},{'_id': False} )
    for security in portfolio:
        send_message(sender_id, dumps(security, indent=4))


# Get existing portfolio
def get_portfolio():
    portfolio = dumps(mongo.db.portfolio.find( {},{'_id': False} ))
    return json.loads(portfolio)

# Insert into db
def send_create_message(sender_id, data):
    mongo.db.portfolio.insert( data )
    send_message(sender_id, "Positions successfully updated :)")

# Update db
def send_update_message(sender_id, data):
    record = mongo.db.portfolio.find_one( {"ticker": data["ticker"]} )
    record["quantity"] = data["quantity"]
    record["price"] = data["price"]
    mongo.db.portfolio.save(record)
    send_message(sender_id, "Positions successfully updated :)")

# Delete from db
def send_delete_message(sender_id, ticker):
    record = mongo.db.portfolio.find_one( {"ticker": ticker} )
    mongo.db.portfolio.remove(record)
    send_message(sender_id, "Positions successfully updated :)")

@app.route('/')
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

@app.route('/test', methods=['POST'])
def test():
    data = request.json
    mongo.db.portfolio.insert( data )

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

                    if message_text.split()[0] in ["ANALYSIS", "PORTFOLIO", "HELP"]:
                        if message_text == "ANALYSIS":
                            pass
                        elif message_text.split()[0] == "PORTFOLIO":
                            if message_text.split()[1] == "SHOW":
                                send_portfolio(sender_id)
                            elif message_text.split()[1] in ["BUY", "SELL"] and len(message_text.split()) == 4:
                                ticker = message_text.split()[2]
                                qty = message_text.split()[3]

                                try:
                                    log(ticker)
                                    log(qty)
                                    log(message_text.split()[1])
                                    blackrock.portfolio(ticker, qty, message_text.split()[1], sender_id)
                                except Exception as e:
                                    send_message(sender_id, "Something went wrong :( Please try again!")
                                    log(traceback.print_exc())
                                    pass
          
                        elif message_text == "HELP":
                            send_help_message(sender_id)
                        else:
                            send_greeting_message(sender_id)

                    else:

                        luis_response = get_response_from_luis_api(message_text)
                        expected_intent = luis_response["intents"][0]["intent"]

                        if expected_intent in ["buySecurity", "sellSecurity"]:
                            if luis_response["intents"][0]["actions"][0]["parameters"]:
                                param_dict = {}
                                params = luis_response["intents"][0]["actions"][0]["parameters"]
                                for param in params:
                                    if param["name"].upper() in ["QUANTITY", "TICKER", "TRADE_TYPE"] and param["value"][0]["entity"]:
                                        param_dict[param["name"]] = str(param["value"][0]["entity"]).upper()

                                        log(param_dict)

                                    if len(param_dict) == 3:
                                        try:
                                            blackrock.portfolio(param_dict["ticker"], param_dict["quantity"], param_dict["trade_type"], sender_id)
                                        except Exception as e:
                                            send_message(sender_id, "Something went wrong :( Please try again!")
                                            log(traceback.print_exc())
                                            pass
                        elif expected_intent == "showPortfolio":
                            send_portfolio(sender_id)
                        elif expected_intent == "greetings":
                            send_greeting_message(sender_id)
                        elif expected_intent == "riskAnalysis":
                            pass # for now
                        else:
                            send_message(sender_id, "Sorry, didn't catch that :( Please use the help menu to use the default operations!")
                            send_help_message(sender_id)


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
