from datetime import datetime
from slack_sdk import WebClient
from src.retrievers.abc import Retriever
from typing import TYPE_CHECKING
from src.docs import SlackConvo

if TYPE_CHECKING:
    from src.config import Config


class SlackRetriever(Retriever):

    def __init__(self, config: 'Config'):
        self.client = WebClient(token=config.SLACK_TOKEN)
        self.workspace_url = self.client.auth_test()['url']
        super().__init__(
            data_file=config.file_slack,
            doc_type=SlackConvo,
            scraping_kwargs={'client': self.client}
        )

    def _fetch_docs(self):
        channels = self.client.conversations_list()["channels"]

        for channel in channels:
            if not channel['is_member']:
                self.client.conversations_join(channel=channel['id'])

        for channel in channels:
            channel_id = channel['id']
            channel_name = channel['name']
            messages = self.client.conversations_history(channel=channel_id)['messages']

            for message in messages:
                timestamp = float(message['ts'])
                legible_timestamp = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                microsecond_timestamp = int(timestamp * 10e6)

                last_edited = datetime.utcfromtimestamp(timestamp)
                if 'latest_reply' in message:
                    last_edited = datetime.utcfromtimestamp(float(message['latest_reply']))

                yield SlackConvo(
                    header=f'Slack message in #{channel_name} from {message["user"]} at {legible_timestamp}',
                    last_edited=last_edited,
                    url=f'{self.workspace_url}.slack.com/archives/{channel_id}/p{microsecond_timestamp}',
                    body=message['text']
                )
