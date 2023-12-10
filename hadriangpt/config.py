import os
import yaml

with open('config.yaml', 'r') as f:
    yaml_config = yaml.safe_load(f)


class Config:

    # from env
    notion_api_key = os.getenv('NOTION_API_KEY')
    slack_token = os.getenv('SLACK_TOKEN')
    slack_signing_secret = os.getenv('SLACK_SIGNING_SECRET')

    # from yaml
    slack_command = yaml_config['slack_command']
    port = yaml_config['port']
    data_dir = yaml_config['data_dir']
    notion_data_file = os.path.join(yaml_config['data_dir'], yaml_config['notion_data_file'])
    embeddings_cache_file = os.path.join(yaml_config['data_dir'], yaml_config['embeddings_cache_file'])
    embeddings_model = yaml_config['embeddings_model']
    query_token_limit = yaml_config['query_token_limit']
    chat_model = yaml_config['chat_model']
    system_prompt_file = yaml_config['system_prompt_file']


if __name__ == "__main__":
    print(dir(Config))
