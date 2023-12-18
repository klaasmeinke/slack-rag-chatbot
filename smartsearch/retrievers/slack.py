from datetime import datetime
from smartsearch.config import Config
from slack_sdk import WebClient
from smartsearch.retrievers import Doc, RetrieverABC

config = Config()
client = WebClient(token=config.SLACK_TOKEN)



# class SlackConversation(Doc):


channels = client.conversations_list()["channels"]

for channel in channels:
    if not channel['is_member']:
        client.conversations_join(channel=channel['id'])

conversations = []

for channel in channels:
    channel_id = channel['id']
    channel_name = channel['name']
    messages = client.conversations_history(channel=channel_id)['messages']

    conversation_header = f'Slack conversation in {channel_name} channel'
    convo = []

    for message in messages:
        if 'reply_count' in message:  # is thread
            conversations.append(convo)
            convo = [message]
            for reply in client.conversations_replies(channel=channel_id, ts=message['ts'])['messages'][1:]:
                convo.append(reply)
            conversations.append(convo)
            convo = []
        else:
            convo.append(message)
    conversations.append(convo)

conversations = [c for c in conversations if c]


def message_to_text(_message: dict):
    dt = datetime.utcfromtimestamp(float(message['ts'])).strftime('%Y-%m-%d %H:%M:%S')
    return f'{_message["user"]} at {dt}: {_message["text"]}'


for convo in conversations:
    print('\n\n\n')
    for msg in convo:
        print(message_to_text(msg))

        # for reply in client.conversations_replies(channel=channel_id, ts=message['ts'])['messages'][1:]:
        #     print(f'\t{reply["text"]}')
