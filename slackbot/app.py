from flask import Flask, request, make_response
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
import requests
from config import config

app = App(token=config.slack_token, signing_secret=config.slack_signing_secret)


@app.command(f"/{config.slack_command}")
def handle_askbot(ack, command):
    ack()

    response_url = command['response_url']

    response_text = call_python_service(command["text"])

    process_command_async(response_text, response_url)

    return {
        "response_type": "in_channel",
        "text": response_text
    }


def call_python_service(message):
    return f"Received: {message}"


def process_command_async(message, response_url):
    response_text = call_python_service(message)

    payload = {
        "response_type": "in_channel",
        "text": response_text
    }

    requests.post(response_url, json=payload)


flask_app = Flask(__name__)
handler = SlackRequestHandler(app)


@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    return handler.handle(request)


if __name__ == "__main__":
    flask_app.run(debug=True, port=config.port)
