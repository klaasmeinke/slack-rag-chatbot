from functools import cached_property
from hadriangpt.config import Config
import hashlib
import tiktoken
from typing import List


class Doc:
    def __init__(self, content: str, config: Config):
        self.content = content
        self.config = config
        self.embedding: List[float] | None = None

    def __str__(self):
        return self.content

    @staticmethod
    def count_tokens(text: str, model_name: str):
        encoding = tiktoken.encoding_for_model(model_name)
        return len(encoding.encode(text))

    @cached_property
    def token_count(self):
        return self.count_tokens(self.content, self.config.chat_model)

    @classmethod
    def create_docs(cls, header: str, body: str, source: str, config: Config) -> List['Doc']:
        header, body = header.strip(), body.strip()
        header_tokens = cls.count_tokens(header, config.chat_model)
        body_tokens = cls.count_tokens(body, config.chat_model)
        if header_tokens + body_tokens <= config.max_doc_tokens:
            return [cls(content=source + '\n' + header + '\n' + body, config=config)]

        encoding = tiktoken.encoding_for_model(config.chat_model)
        body_tokens = encoding.encode(body)

        max_body_tokens = config.max_doc_tokens - header_tokens
        segments = []
        start_idx, end_idx = 0, 0
        while end_idx < len(body_tokens):
            end_idx = min(start_idx + max_body_tokens, len(body_tokens))
            segments.append(encoding.decode(body_tokens[start_idx:end_idx]))
            start_idx += max_body_tokens - config.doc_token_overlap

        segments = ['...' + seg for i, seg in enumerate(segments) if i != 0]
        segments = [seg + '...' for i, seg in enumerate(segments) if i + 1 != len(segments)]

        return [cls(content=header + '\n' + seg, config=config) for seg in segments]

    def set_embedding(self, embedding: List[float]):
        self.embedding = embedding

    @cached_property
    def content_hash(self):
        return hashlib.sha256(self.content.encode()).hexdigest()