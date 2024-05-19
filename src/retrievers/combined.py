"""This retriever combines the other retrievers into one."""

from typing import TYPE_CHECKING

from src.docs import Doc
from src.retrievers.notion import NotionRetriever
from src.retrievers.slack import SlackRetriever
from src.retrievers.type import Retriever

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
        segments = []
        for retriever in self.retrievers:
            segments += retriever.segments
        return segments

    def _fetch_docs(self):
        for retriever in self.retrievers:
            for doc in retriever._fetch_docs():
                yield doc

    def scrape_docs(self):
        for retriever in self.retrievers:
            retriever.scrape_docs()

    def cache_data(self):
        for retriever in self.retrievers:
            retriever.cache_data()

    def load_from_cache(self):
        for retriever in self.retrievers:
            retriever.load_from_cache()
