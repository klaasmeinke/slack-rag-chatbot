import faiss
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
from langchain.docstore import InMemoryDocstore
from langchain.docstore.document import Document
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from pydantic import BaseModel

from typing import List


class VectorDB:
    def __init__(self, max_tokens_per_docs=500):
        # initialize vector database
        embeddings_model = OpenAIEmbeddings()
        embedding_size = 1536
        index = faiss.IndexFlatL2(embedding_size)
        self._vectorstore = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
        self._text_splitter = RecursiveCharacterTextSplitter(chunk_size=max_tokens_per_docs, chunk_overlap=50)

    def add_docs(self, docs):
        if not len(docs):
            return

        self._text_splitter.split_documents(docs)
        sources = list(set([doc.metadata['source'] for doc in docs]))
        for source in sources:
            self._delete_by_source(source)
        self._vectorstore.add_documents(docs)

    def _delete_by_source(self, page):
        # look up docs by source
        d = self._vectorstore.docstore._dict
        to_delete = []
        for key in d:
            if d[key].metadata['source'] == page:
                to_delete.append(key)

        if not to_delete:
            return

        self._vectorstore.delete(to_delete)

    def as_retriever(self):
        return self._vectorstore.as_retriever()


class Doc(BaseModel):
    content: str
    source: str


class Bot:
    def __init__(self, openai_model: str = "gpt-4-1106-preview"):
        llm = ChatOpenAI(model_name=openai_model, temperature=0.1)
        self._vectorstore = VectorDB()
        self.chain = RetrievalQAWithSourcesChain.from_chain_type(llm=llm, retriever=self._vectorstore.as_retriever())

    def __call__(self, question: str):
        return self.chain({"question": question})

    def add_docs(self, docs: List[Doc]):
        self._vectorstore.add_docs([
            Document(page_content=doc.content, metadata={'source': doc.source}) for doc in docs
        ])


if __name__ == "__main__":
    bot = Bot()
    bot.add_docs([
        Doc(content="The meaning of life is 42", source="42-c-4"),
        Doc(content="The meaning of life is 69", source="42-c-5")
    ])
    print(bot("What is the meaning of life?"))
    print(bot("What is the meaning of life?"))
