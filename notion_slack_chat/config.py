import argparse
import os


class Config:
    def __init__(self, args: argparse.Namespace | None = None, validate: bool = True):

        self.NOTION_API_KEY = None
        self.OPENAI_ORG = None
        self.OPENAI_API_KEY = None
        self.SLACK_TOKEN = None
        self.SLACK_SIGNING_SECRET = None

        self.data_refresh_minutes = 60
        self.doc_token_overlap = 50
        self.doc_token_limit = 500
        self.file_embeddings = 'data/embeddings.json'
        self.file_notion = 'data/notion.json'
        self.file_system_prompt = 'resources/system_prompt.txt'
        self.model_chat = 'gpt-3.5-turbo'
        self.model_embeddings = 'text-embedding-ada-002'
        self.model_temperature = 0.1
        self.port = 8000
        self.openai_token_limit = 2000

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

        if self.data_refresh_minutes < 5:
            raise ValueError(
                f'{self.data_refresh_minutes} ({self.data_refresh_minutes}) should be greater than or equal to 5.'
            )

    def help_message(self, config_value: str):
        mapping = {
            'NOTION_API_KEY': 'API key for Notion integration.',
            'OPENAI_ORG': 'Organization ID for OpenAI.',
            'OPENAI_API_KEY': 'API key for OpenAI services.',
            'SLACK_TOKEN': 'Token for Slack bot integration',
            'SLACK_SIGNING_SECRET': 'Signing secret for Slack notion_slack_chat.',
            'data_refresh_minutes': 'Interval in minutes for data refresh (scraping notion, slack etc.).',
            'doc_token_overlap': 'Number of overlapping tokens in retriever documents.',
            'doc_token_limit': 'Limit for the number of tokens in one retriever document.',
            'file_embeddings': 'File path for storing embeddings data.',
            'file_notion': 'File path for storing Notion data.',
            'file_system_prompt': 'File path for the system prompt text',
            'model_chat': 'Model identifier for the OpenAI chat model.',
            'model_embeddings': 'Model identifier for the OpenAI embeddings model.',
            'model_temperature': 'Temperature setting for the chat model.',
            'port': 'Port on which the application runs.',
            'openai_token_limit': 'Token limit for OpenAI API chat requests.',
        }

        message = mapping.get(config_value, f'set {config_value}')
        if getattr(self, config_value):
            message += f' (default: {getattr(self, config_value)})'
        else:
            message += f' (required environmental variable or command line argument)'
        return message
