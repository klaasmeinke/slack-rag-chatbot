from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
import uvicorn

from smartsearch.chat_interfaces.abstract import ChatInterface


class SlackInterface(ChatInterface):
    def __call__(self):
        app = FastAPI()
        slack_app = App(token=self.config.SLACK_TOKEN, signing_secret=self.config.SLACK_SIGNING_SECRET)
        handler = SlackRequestHandler(slack_app)

        @slack_app.message(".*")
        def message_handler(message, say):
            prompt = message['text']
            user_id = message['user']
            response = self.get_response(prompt=prompt, user_id=user_id)
            say(response)

        @app.post("/slack/events")
        async def slack_events(request: Request):
            return await handler.handle(request)

        uvicorn.run(app, host="0.0.0.0", port=self.config.port)
