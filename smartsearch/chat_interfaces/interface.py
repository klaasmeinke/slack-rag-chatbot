from abc import ABC, abstractmethod
from collections import defaultdict
from smartsearch.docselector import DocSelector
from openai import OpenAI
from typing import Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from smartsearch.config import Config


class Interface(ABC):
    def __init__(self, config: 'Config'):
        self.doc_selector = DocSelector(config)
        self.openai_client = OpenAI(api_key=config.OPENAI_API_KEY, organization=config.OPENAI_ORG)
        self.config = config
        self.history: Dict[str, List[Dict[str, str]]] = defaultdict(list)
        with open(config.file_system_prompt) as f:
            self.system_prompt = f.read()

    @abstractmethod
    def __call__(self):
        """ accept user prompts and send responses """

    def get_response(self, prompt: str, user_id: str) -> str:
        self.history[user_id].append({'role': 'user', 'content': prompt})
        docs = self.doc_selector(prompt)
        docs_string = '\n\n'.join([str(doc) for doc in docs])
        system_prompt = self.system_prompt.replace('{docs}', docs_string)

        completion = self.openai_client.chat.completions.create(
            model=self.config.model_chat,
            temperature=self.config.model_temperature,
            messages=[{"role": "system", "content": system_prompt}] + self.history[user_id][-5:]
        )
        response = completion.choices[0].message.content
        self.history[user_id].append({'role': 'assistant', 'content': response})

        return response