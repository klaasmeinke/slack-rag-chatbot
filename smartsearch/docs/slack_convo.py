from datetime import datetime
from smartsearch.docs import Doc
from slack_sdk import WebClient


class SlackConvo(Doc):

    def __init__(self, message: dict, channel_id: str, channel_name: str):
        self.channel_id = channel_id
        self.timestamp = message['ts']
        self.is_thread = 'reply_count' in message

        dt_timestamp = datetime.utcfromtimestamp(float(self.timestamp))
        time_string = dt_timestamp.strftime("%Y-%m-%d %H:%M:%S")
        super().__init__(
            header=f'Message in {channel_name} from {message["user"]} at {time_string}',
            last_edited=dt_timestamp,
            url=f'https://hadrian-group.slack.com/archives/{channel_id}/p{self.timestamp.replace(".", "")}',
            body=message['text'],
            last_scraped=datetime.now()
        )

    def scrape_doc(self, client: WebClient):
        if not self.is_thread:
            return

        replies = client.conversations_replies(channel=self.channel_id, ts=self.timestamp)['messages'][1:]
        for reply in replies:
            reply_time = datetime.utcfromtimestamp(float(self.timestamp)).strftime("%Y-%m-%d %H:%M:%S")
            reply_user = reply["user"]
            reply_text = reply["text"]
            self.body += f'\n\nReply from {reply_user} at {reply_time}\n{reply_text}'


