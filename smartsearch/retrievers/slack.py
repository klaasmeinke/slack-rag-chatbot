from smartsearch.config import Config
from slack_sdk import WebClient

config = Config()
client = WebClient(token=config.SLACK_TOKEN)


channels = client.conversations_list()["channels"]

for channel in channels:
    if not channel['is_member']:
        client.conversations_join(channel=channel['id'])

for channel in channels:
    channel_id = channel['id']
    channel_name = channel['name']
    messages = client.conversations_history(channel=channel_id)['messages']
    for message in messages:

        if 'reply_count' not in message:
            continue

        print(message)

        # for reply in client.conversations_replies(channel=channel_id, ts=message['ts'])['messages'][1:]:
        #     print(f'\t{reply["text"]}')
