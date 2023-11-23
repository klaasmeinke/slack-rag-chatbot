# SlackBot

## Commands
pipenv run run-slack-bot -  Start the slackbot
pipenv run build-docker - Build the docker to deploy the bot

### Install dependencies
pipenv install

### Generate updated requirement file
pipenv run pip freeze > requirements.txt


## Debugging

### Sending manual message
```curl -X POST http://localhost:5000/slack/events \
-H "Content-Type: application/json" \
-d '{
    "token": "your-slack-verification-token",
    "team_id": "T025818FKRP",
    "team_domain": "example",
    "channel_id": "C2147483705",
    "channel_name": "test",
    "user_id": "U028Q807PEZ",
    "user_name": "Steve",
    "command": "/askbot",
    "text": "Your message here",
    "response_url": "http://localhost:5000/response",
    "trigger_id": "13345224609.738474920.8088930838d88f008e0"
}'```

Update the token and response_url in the above example

### Requirements

To be able to let slack access the local running app you could use NGROK to setup a proxy.

```brew install ngrok/ngrok/ngrok```

To start a local tunnel to let Slack connect to your local machine
```ngrok http 8000```