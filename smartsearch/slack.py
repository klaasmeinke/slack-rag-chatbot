from smartsearch.config import Config
from slack_sdk import WebClient

config = Config()
client = WebClient(token=config.SLACK_TOKEN)


channels = client.conversations_list()["channels"]
channel_ids = [channel['id'] for channel in channels]
channels_to_join = [channel['id'] for channel in channels if not channel['is_member']]

for channel_id in channels_to_join:
    client.conversations_join(channel=channel_id)

for channel_id in channel_ids:
    messages = client.conversations_history(channel=channel_id)['messages']
    for message in messages:
        print(message['text'])
        if 'reply_count' not in message:
            continue

        for reply in client.conversations_replies(channel=channel_id, ts=message['ts'])['messages'][1:]:
            print(f'\t{reply["text"]}')
