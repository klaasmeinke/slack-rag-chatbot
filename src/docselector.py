from src.docs import Doc
from src.retrievers import CombinedRetriever
import json
import numpy as np
from tqdm import tqdm
from typing import Dict, List, TYPE_CHECKING
from openai import OpenAI
import os

if TYPE_CHECKING:
    from src.config import Config


class DocSelector:
    def __init__(self, config: 'Config'):
        self.config = config
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, organization=config.OPENAI_ORG)
        self.docs: List[Doc] = []
        self.fetch_doc_embeddings()

    def __call__(self, query: str) -> List[Doc]:
        query_embedding = self.fetch_embedding(query)
        query_vector = np.asarray(query_embedding)
        query_vector_norm = query_embedding / np.linalg.norm(query_vector)

        assert self.docs, 'no docs retrieved'
        docs = [doc for doc in self.docs if doc.embedding]
        assert docs, 'no docs with embeddings retrieved'

        embeddings_matrix = np.asarray([doc.embedding for doc in docs])
        embeddings_matrix_norm = embeddings_matrix / np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        similarities = embeddings_matrix_norm.dot(query_vector_norm)

        selected_docs = []
        token_count = 0

        for i in np.argsort(similarities)[::-1]:
            doc = docs[i]
            token_count += doc.token_count(self.config.model_chat)
            if token_count > self.config.openai_token_limit:
                break
            selected_docs.append(doc)

        return selected_docs

    def load_docs_from_data(self):
        """read docs and embeddings from files. split the docs and assign embeddings to docs."""
        retriever = CombinedRetriever(config=self.config)
        self.docs = retriever.segments
        embeddings_cache = self.load_embeddings_cache()

        for doc in self.docs:
            embedding = embeddings_cache.get(doc.content_hash)
            doc.set_embedding(embedding)

    def refresh_data(self):
        retriever = CombinedRetriever(self.config)
        retriever.scrape_docs()
        self.fetch_doc_embeddings()

    def fetch_doc_embeddings(self):
        self.load_docs_from_data()
        embeddings_cache = self.load_embeddings_cache()
        docs_without_embeddings = [doc for doc in self.docs if doc.content_hash not in embeddings_cache]

        for doc in tqdm(docs_without_embeddings, desc='Fetching Embeddings', disable=not docs_without_embeddings):
            if doc.content_hash in embeddings_cache:
                continue
            embeddings_cache[doc.content_hash] = self.fetch_embedding(str(doc))  # batching doesn't work with azure
            self.save_embeddings_cache(embeddings_cache)

    def fetch_embedding(self, text: str):
        text = text.replace("\n", " ").strip()
        return self.openai_client.embeddings.create(input=[text], model=self.config.model_embeddings).data[0].embedding

    def save_embeddings_cache(self, cache: Dict[str, List[float]]):
        directory = os.path.dirname(self.config.file_embeddings)
        if directory:
            os.makedirs(directory, exist_ok=True)

        with open(self.config.file_embeddings, 'w') as f:
            json.dump(cache, f)

    def load_embeddings_cache(self) -> Dict[str, List[float]]:
        if not os.path.exists(self.config.file_embeddings):
            return dict()
        with open(self.config.file_embeddings) as json_file:
            return json.load(json_file)


def test():
    from src.config import Config
    config = Config()

    selector = DocSelector(config)
    selector.fetch_doc_embeddings()

    docs = selector('What resources do we have for LLama?')
    print('\n\n\n'.join([str(doc) for doc in docs]))


if __name__ == "__main__":
    test()
