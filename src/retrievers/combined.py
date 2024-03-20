"""This retriever combines the other retrievers into one."""

from src.docs import Doc
from src.retrievers.abc import Retriever
from src.retrievers.notion import NotionRetriever
from src.retrievers.slack import SlackRetriever
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config


class CombinedRetriever(Retriever):
    def __init__(self, config: 'Config'):
        self.config = config
        self.retrievers = [NotionRetriever(config), SlackRetriever(config)]

    @property
    def docs(self) -> dict[str, 'Doc']:
        docs = dict()
        for retriever in self.retrievers:
            docs.update(retriever.docs)
        return docs

    @property
    def segments(self) -> list['Doc']:
        """returns docs that are split into smaller segments"""
        docs = list(self.docs.values())
        segments = [seg for doc in docs for seg in doc.split_into_segments(config=self.config)]
        return segments

    def _fetch_docs(self):
        for retriever in self.retrievers:
            for doc in retriever._fetch_docs():
                yield doc

    def scrape_docs(self):
        for retriever in self.retrievers:
            retriever.scrape_docs()

    def save_data(self):
        for retriever in self.retrievers:
            retriever.save_data()

    def load_from_data(self):
        for retriever in self.retrievers:
            retriever.load_from_data()
