import argparse
from hadriangpt.bot import Bot
from hadriangpt.config import Config
from fastapi import FastAPI, Request
import requests
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
import uvicorn


def parse_cli_args():
    parser = argparse.ArgumentParser()
    _config = Config(validate=False)
    for arg, val in vars(_config).items():
        arg_type = type(val) if val is not None else str
        parser.add_argument(f"--{arg}", type=arg_type, help=_config.help_message(arg))
    return parser.parse_args()


args = parse_cli_args()
config = Config(args)
bot = Bot(config)

app = FastAPI()
slack_app = App(token=config.SLACK_TOKEN, signing_secret=config.SLACK_SIGNING_SECRET)
handler = SlackRequestHandler(slack_app)


@slack_app.command(f"/{config.slack_command}")
def handle_askbot(ack, command):
    ack()
    response_url = command['response_url']
    prompt = command["text"]

    response = bot(prompt)
    payload = {
        "response_type": "in_channel",
        "text": response
    }
    requests.post(response_url, json=payload)


@app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)


uvicorn.run(app, host="0.0.0.0", port=config.port)
