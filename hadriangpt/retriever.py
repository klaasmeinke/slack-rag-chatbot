from hadriangpt.docs import Doc
from hadriangpt.config import Config
import json
import numpy as np
from tqdm import tqdm
from typing import Dict, List
from openai import OpenAI
import os
from hadriangpt.notion import Notion


class Retriever:
    def __init__(self, config: Config):
        self.config = config
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, organization=config.OPENAI_ORG)
        self.docs: List[Doc] = []
        self.add_notion_pages()

    def __call__(self, query: str) -> List[str]:
        query_embedding = self.fetch_embedding(query)
        query_vector = np.asarray(query_embedding)
        query_vector_norm = query_embedding / np.linalg.norm(query_vector)

        embeddings_matrix = np.asarray([doc.embedding for doc in self.docs])
        embeddings_matrix_norm = embeddings_matrix / np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        similarities = embeddings_matrix_norm.dot(query_vector_norm)

        token_count, selected_strings = 0, []
        for i in np.argsort(similarities)[::-1]:
            doc = self.docs[i]
            token_count += doc.token_count
            if token_count > self.config.query_token_limit:
                break
            selected_strings.append(str(doc))

        return selected_strings

    def add_notion_pages(self):
        notion = Notion(self.config)
        for page in notion.pages.values():
            if not str(page).strip():
                continue
            self.docs += Doc.create_docs(header=page.header, body=page.content, source=page.url, config=self.config)
        self.add_embeddings_to_docs()

    def add_embeddings_to_docs(self):
        embeddings_cache = self.load_embeddings_cache()
        docs_without_embeddings = [doc for doc in self.docs if doc.content_hash not in embeddings_cache]
        for doc in tqdm(docs_without_embeddings, desc='Fetching Embeddings', disable=not docs_without_embeddings):
            if doc.content_hash in embeddings_cache:
                continue
            embeddings_cache[doc.content_hash] = self.fetch_embedding(doc.content)
            self.save_embeddings_cache(embeddings_cache)

        # add embeddings to docs
        for doc in self.docs:
            doc.set_embedding(embeddings_cache[doc.content_hash])

    def fetch_embedding(self, text: str):
        text = text.replace("\n", " ").strip()
        return self.openai_client.embeddings.create(input=[text], model=self.config.embeddings_model).data[0].embedding

    def save_embeddings_cache(self, cache: Dict[str, List[float]]):
        directory = os.path.dirname(self.config.embeddings_cache_file)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(self.config.embeddings_cache_file, 'w') as f:
            json.dump(cache, f)

    def load_embeddings_cache(self) -> Dict[str, List[float]]:
        if os.path.exists(self.config.embeddings_cache_file):
            with open(self.config.embeddings_cache_file) as json_file:
                return json.load(json_file)
        return dict()


def test():
    config = Config()
    retriever = Retriever(config)
    docs = retriever('What resources do we have for LLama?')
    for doc in docs:
        print(doc)


if __name__ == "__main__":
    test()
