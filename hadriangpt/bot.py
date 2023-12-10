from hadriangpt.config import Config
from hadriangpt.retriever import Retriever
from openai import OpenAI


class Bot:
    def __init__(self):
        self.retriever = Retriever()
        self.openai_client = OpenAI()
        with open(Config.system_prompt_file) as f:
            self.system_prompt = f.read()

    def __call__(self, query: str):
        docs = self.retriever(query)
        doc_string = '\n\n'.join(docs)
        system_prompt = self.system_prompt.replace('{docs}', doc_string)

        print(system_prompt)

        completion = self.openai_client.chat.completions.create(
            model=Config.chat_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        return completion.choices[0].message.content


def test():
    """Chat with bot from cli."""
    bot = Bot()

    while True:
        query = input('Query: ')
        if query.lower().strip() == 'exit':
            return
        print(f'Response: {bot(query)}\n')


if __name__ == "__main__":
    test()
