from hadriangpt.config import Config
from hadriangpt.retriever import Retriever
from openai import OpenAI


class Bot:
    def __init__(self, config: Config):
        self.retriever = Retriever(config)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, organization=config.OPENAI_ORG)
        self.config = config
        with open(config.system_prompt_file) as f:
            self.system_prompt = f.read()

    def __call__(self, query: str):
        docs = self.retriever(query)
        doc_string = '\n\n'.join(docs)
        system_prompt = self.system_prompt.replace('{docs}', doc_string)

        completion = self.openai_client.chat.completions.create(
            model=self.config.chat_model,
            temperature=self.config.model_temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        )
        return completion.choices[0].message.content


def test():
    """Chat with bot from cli."""
    config = Config()
    bot = Bot(config)

    while True:
        query = input('Query: ')
        if query.lower().strip() == 'exit':
            return
        print(f'Response: {bot(query)}\n')


if __name__ == "__main__":
    test()
