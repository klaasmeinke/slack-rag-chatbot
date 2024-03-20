from abc import ABC, abstractmethod
from datetime import datetime
from functools import cached_property
import hashlib
import tiktoken
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config


class Doc(ABC):
    def __init__(
            self,
            body: str,
            header: str,
            url: str,
            last_edited: datetime | str,
            last_scraped: datetime | str = datetime.min,
    ):
        """used to store information from different sources."""
        body, header, url = body.strip(), header.strip(), url.strip()

        if isinstance(last_edited, str):
            last_edited = datetime.fromisoformat(last_edited)
        if isinstance(last_scraped, str):
            last_scraped = datetime.fromisoformat(last_scraped)

        self.body = body
        self.header = header
        self.last_edited = last_edited
        self.last_scraped = last_scraped
        self.url = url
        self.embedding: list[float] | None = None

    def __str__(self):
        return '\n'.join([self.header, self.body])

    def scrape(self, **kwargs):
        if self.is_scraped:
            return
        self._scrape(**kwargs)
        self.last_scraped = datetime.utcnow()

    @abstractmethod
    def _scrape(self, **kwargs):
        """scrape the doc and add info to self.body"""

    @property
    def is_scraped(self):
        return self.last_scraped >= self.last_edited

    @staticmethod
    def count_tokens(text: str, model: str):
        encoding = tiktoken.encoding_for_model(model)
        return len(encoding.encode(text))

    def token_count(self, model: str):
        return self.count_tokens(str(self), model)

    def split_into_segments(self, config: 'Config') -> list['Doc']:
        if not self.body:
            return []  # add logging here

        body_tokens = self.count_tokens(self.body, config.model_chat)
        header_tokens = self.count_tokens(self.header, config.model_chat)
        url_tokens = self.count_tokens(self.url, config.model_chat)
        total_tokens = sum([body_tokens, header_tokens, url_tokens])

        if total_tokens <= config.doc_token_limit:
            doc = self.__class__(
                body=self.body,
                header=self.header,
                last_edited=self.last_edited,
                last_scraped=self.last_scraped,
                url=self.url
            )
            return [doc]

        encoding = tiktoken.encoding_for_model(config.model_chat)
        body_tokens = encoding.encode(self.body)
        max_body_tokens = config.doc_token_limit - header_tokens - url_tokens

        if max_body_tokens < 50:
            return []  # add logging here

        segments = []
        start_idx, end_idx = 0, 0
        while end_idx < len(body_tokens):
            end_idx = min(start_idx + max_body_tokens, len(body_tokens))
            segments.append(encoding.decode(body_tokens[start_idx:end_idx]))
            start_idx += max_body_tokens - config.doc_token_overlap

        segments = ['...' + seg for i, seg in enumerate(segments) if i != 0]
        segments = [seg + '...' for i, seg in enumerate(segments) if i + 1 != len(segments)]

        return [
            self.__class__(
                body=seg,
                header=self.header,
                url=self.url,
                last_edited=self.last_edited,
                last_scraped=self.last_scraped
            )
            for seg in segments
        ]

    def set_embedding(self, embedding: list[float]):
        self.embedding = embedding

    @cached_property
    def content_hash(self):
        content = '\n'.join([self.header, self.body])
        return hashlib.sha256(content.encode()).hexdigest()

    def save_to_dict(self) -> dict[str, str]:
        return {
            'body': self.body,
            'header': self.header,
            'last_edited': self.last_edited.isoformat(),
            'last_scraped': self.last_scraped.isoformat(),
            'url': self.url,
        }

    def update_from_doc(self, doc: 'Doc'):
        assert self.url == doc.url, "can only update from another doc that has the same url"

        if doc.last_edited > self.last_edited:
            self.last_edited = doc.last_edited
            self.header = doc.header

        if doc.last_scraped > self.last_scraped:
            self.last_scraped = doc.last_scraped
            self.body = doc.body
