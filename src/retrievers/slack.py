from datetime import datetime
from functools import cached_property
from typing import TYPE_CHECKING

from slack_sdk import WebClient

from src.docs import SlackConvo
from src.retrievers.type import Retriever

if TYPE_CHECKING:
    from src.config import Config


class SlackRetriever(Retriever):

    def __init__(self, config: 'Config'):
        self.client = WebClient(token=config.SLACK_TOKEN)
        super().__init__(
            cache_file=config.file_slack,
            config=config,
            doc_type=SlackConvo,
            scraping_kwargs={'client': self.client}
        )

    @cached_property
    def workspace_url(self):
        return self.client.auth_test()['url']

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
                    url=f'{self.workspace_url}archives/{channel_id}/p{microsecond_timestamp}',
                    body=message['text']
                )
