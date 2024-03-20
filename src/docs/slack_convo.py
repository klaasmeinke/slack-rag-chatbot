from datetime import datetime
from src.docs import Doc
from slack_sdk import WebClient


class SlackConvo(Doc):

    def __init__(self, **kwargs):
        url = kwargs['url']
        self.channel_id = url.split('/')[-2]
        self.unix_timestamp = int(url.split('/')[-1].removeprefix('p')) / 10e6
        self.dt_timestamp = datetime.utcfromtimestamp(self.unix_timestamp)

        super().__init__(**kwargs)

    @property
    def is_thread(self) -> bool:
        return self.last_edited > self.dt_timestamp

    def _scrape(self, client: WebClient):
        if not self.is_thread:
            return

        replies = client.conversations_replies(channel=self.channel_id, ts=self.unix_timestamp)['messages'][1:]
        for reply in replies:
            reply_time = datetime.utcfromtimestamp(float(reply['ts'])).strftime("%Y-%m-%d %H:%M:%S")
            reply_user = reply["user"]
            reply_text = reply["text"]
            self.body += f'\nReply from {reply_user} at {reply_time}: {reply_text}'


def test():
    data_dict = {
        "body": "Team, the latest update for Project Unicorn is now live. Please review the changes in the shared document and add your feedback by EOD Thursday.",
        "header": "Message in general from U06AULNMWJV at 2023-12-16 09:41:32",
        "last_edited": "2023-12-16T09:41:55.573119",
        "last_scraped": "2000-12-27T11:57:43.927129",
        "url": "https://hadrian-group.slack.com/archives/C06AJFBNSDS/p17027196926058590"
    }
    convo = SlackConvo(**data_dict)
    print(convo.is_thread)
    print(convo)
    print()
    from src.config import Config
    config = Config()
    client = WebClient(token=config.SLACK_TOKEN)
    convo.scrape(client=client)
    print(convo)


if __name__ == "__main__":
    test()
