from abc import ABC, abstractmethod
import json
from smartsearch.retrievers.docs import Doc
import os
from tqdm import tqdm
from typing import Dict, List


class RetrieverABC(ABC):
    def __init__(
            self,
            data_file: str,
            doc_type: type(Doc),
            scraping_kwargs: dict = None,
    ):
        self.data_file = data_file
        self.doc_type = doc_type
        self.scraping_kwargs = scraping_kwargs if scraping_kwargs else dict()

        self.docs: Dict[str, doc_type] = dict()
        self.load_from_data()

    @abstractmethod
    def fetch_docs(self):
        """add docs to self.docs using self.add_doc (without scraping)"""

    def scrape_docs(self):
        unscraped_docs = [doc.url for doc in self.docs.values() if not doc.is_scraped]
        for url in tqdm(unscraped_docs, desc=type(self).__name__, disable=not unscraped_docs):
            self.docs[url].scrape(**self.scraping_kwargs)
            self.save_data()

    def add_doc(self, doc: Doc):
        if doc.url in self.docs:
            self.docs[doc.url].update_from_doc(doc)
        else:
            self.docs[doc.url] = doc

    def save_data(self):
        directory = os.path.dirname(self.data_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        data = [p.save_to_dict() for p in self.docs.values()]
        with open(self.data_file, 'w') as f:
            json.dump(data, f)

    def load_from_data(self):
        if not os.path.exists(self.data_file):
            return
        with open(self.data_file) as json_file:
            data: List[Dict[str, str]] = json.load(json_file)
        for doc_data in data:
            doc = self.doc_type.load_from_dict(doc_data)
            self.add_doc(doc)
