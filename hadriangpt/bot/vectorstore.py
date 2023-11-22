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
        page_urls = list(set([doc.metadata['page_url'] for doc in docs]))
        for page in page_urls:
            self._delete_by_page_url(page)
        self._vectorstore.add_documents(docs)

    def _delete_by_page_url(self, page):
        # look up docs by source
        d = self._vectorstore.docstore._dict
        to_delete = []
        for key in d:
            if d[key].metadata['page_url'] == page:
                to_delete.append(key)

        if not to_delete:
            return

        self._vectorstore.delete(to_delete)

    def as_retriever(self):
        return self._vectorstore.as_retriever()
