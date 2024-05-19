import json
import os
from abc import ABC, abstractmethod
from typing import Generator, TYPE_CHECKING

from tqdm import tqdm

from src.docs.type import Doc

if TYPE_CHECKING:
    from src.config import Config


class Retriever(ABC):
    def __init__(
            self,
            cache_file: str,
            config: 'Config',
            doc_type: type(Doc),
            scraping_kwargs: dict = None,
    ):
        self.cache_file = cache_file
        self.config = config
        self.doc_type = doc_type
        self.scraping_kwargs = scraping_kwargs if scraping_kwargs else dict()

        self.docs: dict[str, doc_type] = dict()
        try:
            self.load_from_cache()
        except FileNotFoundError as e:
            print(f'{e}. Scraping...')
            self.scrape_docs()

    @abstractmethod
    def _fetch_docs(self) -> Generator[Doc, None, None]:
        """fetch all docs that exist for this data source (without scraping)"""

    def scrape_docs(self):
        for doc in self._fetch_docs():
            self.add_doc(doc)
        self.cache_data()

        unscraped_docs = [doc for doc in self.docs.values() if not doc.is_scraped]
        for doc in tqdm(unscraped_docs, desc=type(self).__name__, disable=not unscraped_docs):
            doc.scrape(**self.scraping_kwargs)
            self.cache_data()

    def add_doc(self, doc: Doc):
        if doc.url in self.docs:
            self.docs[doc.url].update_from_doc(doc)
        else:
            self.docs[doc.url] = doc

    def cache_data(self):
        directory = os.path.dirname(self.cache_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        data = [p.save_to_dict() for p in self.docs.values()]

        with open(self.cache_file, 'w') as f:
            json.dump(data, f)

    def load_from_cache(self):
        if not os.path.exists(self.cache_file):
            raise FileNotFoundError('Cache file not found.')
        with open(self.cache_file) as json_file:
            data: list[dict[str, str]] = json.load(json_file)
        for doc_data in data:
            doc = self.doc_type(**doc_data)
            self.add_doc(doc)

    @property
    def segments(self) -> list[Doc]:
        return [
            seg for doc in self.docs.values()
            for seg in doc.split_into_segments(config=self.config)
        ]
