from functools import cached_property
from hadriangpt.config import Config
import hashlib
import json
import numpy as np
import tiktoken
from tqdm import tqdm
from typing import Dict, List, Optional
from openai import OpenAI
import os
from pydantic import BaseModel, Field
from hadriangpt.notion import Notion


class Doc(BaseModel):
    content: str = Field(frozen=True)
    source: str = Field(frozen=True)
    embedding: Optional[str] = None

    def __str__(self):
        return self.content

    @cached_property
    def content_hash(self):
        return hashlib.sha256(self.content.encode()).hexdigest()

    @cached_property
    def token_count(self):
        encoding = tiktoken.encoding_for_model(Config.chat_model)
        return len(encoding.encode(self.content))


class Retriever:
    def __init__(self):
        self.openai_client = OpenAI()
        self.docs: Dict[str, Doc] = dict()
        self.embeddings_cache: Dict[str, List[float]] = dict()
        self.load_embedding_file()
        self.add_notion_pages()

    def __call__(self, query: str) -> List[str]:
        query_embedding = self.fetch_embedding(query)
        query_vector = np.asarray(query_embedding)
        query_vector_norm = query_embedding / np.linalg.norm(query_vector)

        embeddings_matrix = np.asarray(list(self.embeddings_cache.values()))
        embeddings_matrix_norm = embeddings_matrix / np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        similarities = embeddings_matrix_norm.dot(query_vector_norm)

        token_count, selected_docs = 0, []
        for index in np.argsort(similarities)[::-1]:
            doc_id = list(self.embeddings_cache.keys())[index]
            doc = self.docs[doc_id]
            token_count += doc.token_count
            if token_count > Config.query_token_limit:
                break
            selected_docs.append(str(doc))

        return selected_docs

    def add_notion_pages(self):
        notion = Notion()
        for page in notion.pages.values():
            if not str(page).strip():
                continue
            doc = Doc(content=str(page), source=page.url)
            self.docs[doc.content_hash] = doc
        self.add_embeddings_to_docs()

    def add_embeddings_to_docs(self):
        # add embeddings to cache
        docs_without_embeddings = {key: doc for key, doc in self.docs.items() if key not in self.embeddings_cache}
        if docs_without_embeddings:
            print('fetching embeddings...')
            for key, doc in tqdm(docs_without_embeddings.items()):
                if key in self.embeddings_cache:
                    continue
                self.embeddings_cache[key] = self.fetch_embedding(doc.content)
                self.save_embeddings_file()

        # add embeddings to docs
        for key, doc in self.docs.items():
            doc.embedding = self.embeddings_cache[key]

    def fetch_embedding(self, text: str):
        text = text.replace("\n", " ")
        return self.openai_client.embeddings.create(input=[text], model=Config.embeddings_model).data[0].embedding

    def save_embeddings_file(self):
        os.makedirs(Config.data_dir, exist_ok=True)
        with open(Config.embeddings_cache_file, 'w') as f:
            json.dump(self.embeddings_cache, f)

    def load_embedding_file(self):
        if os.path.exists(Config.embeddings_cache_file):
            with open(Config.embeddings_cache_file) as json_file:
                self.embeddings_cache = json.load(json_file)


def test():
    retriever = Retriever()
    docs = retriever('What resources do we have for LLama?')
    for doc in docs:
        print(doc)


if __name__ == "__main__":
    test()
