import argparse
import os
from typing import TYPE_CHECKING

from dotenv import load_dotenv

from src.chat_interfaces import CliInterface, SlackInterface
if TYPE_CHECKING:
    from src.chat_interfaces import Interface

load_dotenv()  # take environment variables from .env.


class Config:
    def __init__(self):

        self.NOTION_API_KEY = None
        self.OPENAI_ORG = None
        self.OPENAI_API_KEY = None
        self.SLACK_TOKEN = None
        self.SLACK_SIGNING_SECRET = None

        self.data_refresh_minutes = 60
        self.doc_token_overlap = 50
        self.doc_token_limit = 500
        self.interface = 'cli'
        self.file_embeddings = 'data/embeddings.json'
        self.file_notion = 'data/notion.json'
        self.file_slack = 'data/slack.json'
        self.file_system_prompt = 'resources/system_prompt.txt'
        self.model_chat = 'gpt-3.5-turbo-16k'
        self.model_embeddings = 'text-embedding-ada-002'
        self.model_temperature = 0.3
        self.port = 8000
        self.openai_token_limit = 2000

        # override attributes with env variables
        self.load_env_config()

        # override attributes with cli variables
        self.load_cli_args()

        # validate that all variables are set
        self.validate_config()

    @property
    def interface_map(self):
        return {
            'cli': CliInterface,
            'slack': SlackInterface,
        }

    def get_interface(self) -> 'Interface':
        self.interface = self.interface.lower().strip()
        assert self.interface in self.interface_map, f'interface {self.interface} must be in {list(self.interface_map)}'
        return self.interface_map[self.interface](self)

    def load_cli_args(self):
        parser = argparse.ArgumentParser()
        for arg, val in vars(self).items():
            arg_type = type(val) if val is not None else str
            parser.add_argument(f"--{arg}", type=arg_type, help=self.help_message(arg))

        args = parser.parse_args()
        for key, value in vars(args).items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

    def load_env_config(self):
        for key, value in os.environ.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate_config(self):
        self.get_interface()

        none_attrs = [attr for attr in vars(self) if getattr(self, attr) is None]
        if none_attrs:
            raise ValueError(f'{none_attrs} should be defined in environmental variables or command line arguments.')

        if self.data_refresh_minutes < 5:
            raise ValueError(
                f'{self.data_refresh_minutes} ({self.data_refresh_minutes}) should be greater than or equal to 5.'
            )

    def help_message(self, config_value: str):
        mapping = {
            'NOTION_API_KEY': 'API key for Notion integration.',
            'OPENAI_ORG': 'Organization ID for OpenAI.',
            'OPENAI_API_KEY': 'API key for OpenAI services.',
            'SLACK_TOKEN': 'Token for Slack bot integration.',
            'SLACK_SIGNING_SECRET': 'Signing secret for Slack src.',
            'data_refresh_minutes': 'Interval in minutes for data refresh.',
            'doc_token_overlap': 'Number of overlapping tokens in retriever documents.',
            'doc_token_limit': 'Limit for the number of tokens in one retriever document.',
            'interface': f'How to interact with the bot. Options: {list(self.interface_map)}',
            'file_embeddings': 'File path for storing embeddings data.',
            'file_notion': 'File path for storing Notion data.',
            'file_system_prompt': 'File path for the system prompt text',
            'model_chat': 'Model identifier for the OpenAI chat model.',
            'model_embeddings': 'Model identifier for the OpenAI embeddings model.',
            'model_temperature': 'Temperature setting for the chat model.',
            'port': 'Port on which the application runs.',
            'openai_token_limit': 'Token limit for all docs in system prompt.',
        }

        message = mapping.get(config_value, f'set {config_value}')
        if getattr(self, config_value):
            message += f' (default: {getattr(self, config_value)})'
        else:
            message += f' (required environmental variable or command line argument)'
        return message
