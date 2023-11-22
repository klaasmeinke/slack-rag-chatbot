import faiss
from langchain.docstore import InMemoryDocstore
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS


class VectorDB:
    def __init__(self, max_tokens_per_docs=500):
        # initialize vector database
        embeddings_model = OpenAIEmbeddings()
        embedding_size = 1536
        index = faiss.IndexFlatL2(embedding_size)
        self.vectorstore_public = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
        self.max_tokens_per_doc = 500

    def add_docs(self, docs):
        self.vectorstore_public.add_documents(docs)

    def as_retriever(self):
        return self.vectorstore_public.as_retriever()
