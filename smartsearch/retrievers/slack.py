from slack_sdk import WebClient
from smartsearch.retrievers.abstract import Retriever
from typing import TYPE_CHECKING
from smartsearch.docs import SlackConvo

if TYPE_CHECKING:
    from smartsearch.config import Config


class SlackRetriever(Retriever):

    def __init__(self, config: 'Config'):
        self.client = WebClient(token=config.SLACK_TOKEN)
        super().__init__(
            data_file=config.file_slack,
            doc_type=SlackConvo,
            scraping_kwargs={'client': self.client}
        )

    def docs_generator(self):
        channels = self.client.conversations_list()["channels"]

        for channel in channels:
            if not channel['is_member']:
                self.client.conversations_join(channel=channel['id'])

        for channel in channels:
            channel_id = channel['id']
            channel_name = channel['name']
            messages = self.client.conversations_history(channel=channel_id)['messages']

            for message in messages:
                yield SlackConvo(message=message, channel_id=channel_id, channel_name=channel_name)
