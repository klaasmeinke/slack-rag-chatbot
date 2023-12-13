import argparse
import os


class Config:
    def __init__(self, args: argparse.Namespace | None = None, validate: bool = True):

        self.NOTION_API_KEY = None
        self.SLACK_TOKEN = None
        self.SLACK_SIGNING_SECRET = None
        self.OPENAI_ORG = None
        self.OPENAI_API_KEY = None

        self.model_temperature = 0.1
        self.slack_command = 'hgpt'
        self.port = 8000
        self.data_dir = 'data'
        self.notion_data_file = 'data/notion.json'
        self.embeddings_cache_file = 'data/embeddings.json'
        self.embeddings_model = 'text-embedding-ada-002'
        self.query_token_limit = 2000
        self.chat_model = 'gpt-3.5-turbo'
        self.system_prompt_file = 'resources/system_prompt.txt'
        self.max_doc_tokens = 500
        self.doc_token_overlap = 50

        # override defaults with env variables and cli args
        self.load_env_config()
        self.load_cli_config(args)

        # validate that all variables are set
        if validate:
            self.validate_config()

    def load_env_config(self):
        for key, value in os.environ.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def load_cli_config(self, args: argparse.Namespace | None):
        if args is None:
            return
        for key, value in vars(args).items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)

    def validate_config(self):
        none_attrs = [attr for attr in vars(self) if getattr(self, attr) is None]
        if none_attrs:
            raise ValueError(f'{none_attrs} should be defined in environmental variables or command line arguments.')

    def help_message(self, config_value: str):
        mapping = {
            'slack_command': 'command to use in slack to chat with the bot',
            'port': 'port that the bot is exposed on',
        }

        message = mapping.get(config_value, f'set {config_value}')
        if getattr(self, config_value):
            message += f' (default: {getattr(self, config_value)})'
        else:
            message += f' (required environmental variable or command line argument)'
        return message
