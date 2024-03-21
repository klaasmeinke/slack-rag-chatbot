from abc import ABC, abstractmethod
from collections import defaultdict
from datetime import datetime
from openai import OpenAI
import re
from src.docselector import DocSelector
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.config import Config


class ChatInterface(ABC):
    def __init__(self, config: 'Config'):
        self.doc_selector = DocSelector(config)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, organization=config.OPENAI_ORG)
        self.config = config
        self.history: dict[str, list[dict[str, str]]] = defaultdict(list)
        with open(config.file_system_prompt) as f:
            self.system_prompt = f.read()

    @abstractmethod
    def __call__(self):
        """accept user prompts and send responses."""

    def refresh_data(self):
        self.doc_selector.refresh_data()

    def get_response(self, prompt: str, user_id: str) -> str:
        self.history[user_id].append({'role': 'user', 'content': prompt})
        docs = self.doc_selector(prompt)

        doc_2_id = {doc.url: f'(Document {i})' for i, doc in enumerate(docs)}
        id_2_doc = {f'Document {i}': doc.url for i, doc in enumerate(docs)}

        docs_string = '\n\n'.join([f'{doc_2_id[doc.url]}: {doc}' for doc in docs])
        time_string = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        system_prompt = self.system_prompt.format(docs=docs_string, time=time_string)
        print(system_prompt)

        completion = self.openai_client.chat.completions.create(
            model=self.config.model_chat,
            temperature=self.config.model_temperature,
            messages=[{"role": "system", "content": system_prompt}] + self.history[user_id][-5:]
        )
        response = completion.choices[0].message.content

        response = re.sub(r'<(Document \w+)\|(.*?)>', r'<{\1}|\2>', response)
        response = response.format(**id_2_doc)
        print(response)

        self.history[user_id].append({'role': 'assistant', 'content': response})

        return response


def test(prompt: str):
    from src.config import Config
    import cProfile
    import pstats

    class TestInterface(ChatInterface):
        def __call__(self):
            pass

    config = Config()
    interface = TestInterface(config)

    profiler = cProfile.Profile()
    profiler.enable()

    response = interface.get_response(prompt, user_id='1')

    profiler.disable()
    stats = pstats.Stats(profiler).sort_stats('cumulative')
    stats.print_stats(40)

    print(f'Prompt: {prompt}\nResponse: {response}')


if __name__ == "__main__":
    test('hello')
