import faiss
from langchain.docstore import InMemoryDocstore
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS


class VectorDB:
    def __init__(self, max_tokens_per_docs=500):
        # initialize vector database
        embeddings_model = OpenAIEmbeddings()
        embedding_size = 1536
        index = faiss.IndexFlatL2(embedding_size)
        self._vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
        self._text_splitter = RecursiveCharacterTextSplitter(chunk_size=max_tokens_per_docs, chunk_overlap=50)

    def add_docs(self, docs):
        self._text_splitter.split_documents(docs)
        sources = list(set([doc.metadata['source'] for doc in docs]))
        for source in sources:
            self.delete_by_source(source)
        self._vectorstore.add_documents(docs)

    def delete_by_source(self, source):
        # look up docs by source
        d = self._vectorstore.docstore._dict
        to_delete = []
        for key in d:
            if d[key].metadata['source'] == source:
                to_delete.append(key)

        if not to_delete:
            return

        self._vectorstore.delete(to_delete)

    def as_retriever(self):
        return self._vectorstore.as_retriever()
