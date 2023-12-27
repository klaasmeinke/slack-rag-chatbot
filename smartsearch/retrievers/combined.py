"""This retriever combines the other retrievers into one."""

from smartsearch.docs import Doc
from smartsearch.retrievers.abstract import Retriever
from smartsearch.retrievers.notion import NotionRetriever
from smartsearch.retrievers.slack import SlackRetriever
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from smartsearch.config import Config


class CombinedRetriever(Retriever):
    def __init__(self, config: 'Config'):
        self.config = config
        self.retrievers = [SlackRetriever(config)]
        # self.retrievers = [NotionRetriever(config), SlackRetriever(config)]

    @property
    def docs(self) -> Dict[str, 'Doc']:
        docs = dict()
        for retriever in self.retrievers:
            docs.update(retriever.docs)
        return docs

    @property
    def segments(self) -> List['Doc']:
        """returns docs that are split into smaller segments"""
        docs = list(self.docs.values())
        segments = [seg for doc in docs for seg in doc.get_segments(config=self.config)]
        return segments

    def docs_generator(self):
        for retriever in self.retrievers:
            for doc in retriever.docs_generator():
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
