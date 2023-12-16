from smartsearch.config import Config
from smartsearch.retriever import Retriever
from openai import OpenAI
from typing import Dict, List


class Bot:
    def __init__(self, config: Config):
        self.retriever = Retriever(config)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, organization=config.OPENAI_ORG)
        self.config = config
        with open(config.file_system_prompt) as f:
            self.system_prompt = f.read()

    def __call__(self, history: List[Dict[str, str]] = None):
        retrieval_string = ' '.join([msg['content'] for msg in history[-2:]])
        docs = self.retriever(retrieval_string)
        docs_string = '\n\n'.join(docs)
        system_prompt = self.system_prompt.replace('{docs}', docs_string)

        completion = self.openai_client.chat.completions.create(
            model=self.config.model_chat,
            temperature=self.config.model_temperature,
            messages=[{"role": "system", "content": system_prompt}] + history[-5:]
        )

        return completion.choices[0].message.content


def test():
    """Chat with bot from cli."""
    config = Config()
    bot = Bot(config)

    history: List[Dict[str, str]] = []

    while True:
        prompt = input('Prompt: ')
        history.append({'role': 'user', 'content': prompt})
        if prompt.lower().strip() == 'exit':
            return

        response = bot(history)
        print(f'Response: {response}\n')
        history.append({'role': 'assistant', 'content': response})


if __name__ == "__main__":
    test()
