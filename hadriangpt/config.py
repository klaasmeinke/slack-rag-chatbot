import argparse
import os


class Config:
    def __init__(self, args: argparse.Namespace | None = None):

        self.NOTION_API_KEY = None
        self.SLACK_TOKEN = None
        self.SLACK_SIGNING_SECRET = None
        self.OPENAI_ORG = None
        self.OPENAI_API_KEY = None

        self.slack_command = 'hgpt'
        self.port = 8000
        self.data_dir = 'data'
        self.notion_data_file = 'notion.json'
        self.embeddings_cache_file = 'embeddings.json'
        self.embeddings_model = 'text-embedding-ada-002'
        self.query_token_limit = 2000
        self.chat_model = 'gpt-3.5-turbo'
        self.system_prompt_file = 'resources/system_prompt.txt'

        # override defaults with env variables and cli args
        self.load_env_config()
        self.load_cli_config(args)

        # validate that all variables are set (not None)
        self.validate_config()

    @property
    def notion_data_path(self):
        return os.path.join(self.data_dir, self.notion_data_file)

    @property
    def embeddings_cache_path(self):
        return os.path.join(self.data_dir, self.embeddings_cache_file)

    def help_message(self, config_value: str):
        mapping = {
            'slack_command': 'command to use in slack to chat with the bot',
            'port': 'port that the bot is exposed on',
        }

        assert config_value in vars(self), f'{config_value} is not a valid config value'
        assert all(key in vars(self) for key in mapping), 'mapping dict contains invalid config values'
        return mapping.get(config_value)

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
