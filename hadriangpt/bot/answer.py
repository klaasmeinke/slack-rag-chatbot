from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
import faiss
from langchain.docstore import InMemoryDocstore
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.docstore.document import Document


doc = Document(page_content="The meaning of life is 42", metadata={"source": "local"})


llm = ChatOpenAI(model_name="gpt-4-1106-preview", temperature=0.1)

# embedding model and vector store
embeddings_model = OpenAIEmbeddings()
embedding_size = 1536
index = faiss.IndexFlatL2(embedding_size)
vectorstore_public = FAISS(embeddings_model.embed_query, index, InMemoryDocstore({}), {})
vectorstore_public.add_documents([doc])
qa = RetrievalQA.from_chain_type(llm=llm, retriever=vectorstore_public.as_retriever())


if __name__ == "__main__":
    print(qa("What is the meaning of life?"))
