from smartsearch.retrievers import Doc
from smartsearch.retrievers import NotionRetriever
from smartsearch.retrievers import RetrieverABC
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from smartsearch.config import Config


class Retriever(RetrieverABC):
    def __init__(self, config: 'Config'):
        self.config = config
        self.retrievers = [NotionRetriever(config)]

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

    def fetch_docs(self):
        for retriever in self.retrievers:
            retriever.fetch_docs()

    def scrape_docs(self):
        for retriever in self.retrievers:
            retriever.scrape_docs()

    def add_doc(self, doc: Doc):
        raise TypeError('Adding a doc directly to the Retriever class is not supported.')

    def save_data(self):
        for retriever in self.retrievers:
            retriever.save_data()

    def load_from_data(self):
        for retriever in self.retrievers:
            retriever.load_from_data()
