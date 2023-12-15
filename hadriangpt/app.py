from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import argparse
from hadriangpt.bot import Bot
from hadriangpt.config import Config
from hadriangpt.notion import Notion
from hadriangpt.retriever import Retriever
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from typing import Dict, List
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


# scrape notion and refresh embeddings periodically
def refresh_data():
    Notion(config, fetch_pages=True, scrape_pages=True)
    Retriever(config).add_embeddings_to_docs()


scheduler = BackgroundScheduler()
scheduler.add_job(func=refresh_data, trigger="interval", minutes=config.data_refresh_minutes)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())


history: Dict[str, List[Dict[str, str]]] = dict()


@slack_app.message(".*")
def message_handler(message, say):
    prompt = message['text']
    user_id = message['user']

    if user_id not in history:
        history[user_id] = [{'role': 'user', 'content': prompt}]
    else:
        history[user_id].append({'role': 'user', 'content': prompt})

    response = bot(prompt, history=history[user_id])
    history[user_id].append({'role': 'assistant', 'content': response})

    say(response)


@app.post("/slack/events")
async def slack_events(request: Request):
    return await handler.handle(request)


uvicorn.run(app, host="0.0.0.0", port=config.port)
