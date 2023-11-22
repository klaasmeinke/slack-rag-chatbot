from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.docstore.document import Document
from hadriangpt.bot.vectorstore import VectorDB


class Bot:
    def __init__(self, openai_model: str = "gpt-4-1106-preview"):
        llm = ChatOpenAI(model_name=openai_model, temperature=0.1)
        self._vectorstore = VectorDB()
        self.chain = RetrievalQAWithSourcesChain.from_chain_type(
            llm=llm, retriever=self._vectorstore.as_retriever()
        )

    def run(self, question: str):
        return self.chain({"question": question})

    def add_docs(self, docs):
        self._vectorstore.add_docs(docs)


if __name__ == "__main__":
    bot = Bot()
    bot.add_docs([Document(page_content="The meaning of life is 42", metadata={"source": "42-c"})])
    print(bot.run("What is the meaning of life?"))
    bot.add_docs([Document(page_content="The meaning of life is 69", metadata={"source": "42-c"})])
    print(bot.run("What is the meaning of life?"))
