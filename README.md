# Slack Notion RAG Chatbot

Search through your Slack Pages and Notion Pages using a natural language interface.

This repository integrates with Notion's and Slack's APIs to pull Slack messages and Notion pages.
The chatbot has access to these documents and answers questions using RAG (retrieval-augment-generation).

The chatbot can be accessed from two interfaces: the CLI or Slack.

# Set-Up

### 1. Install the Repo

1. Install Python >= 3.8.
2. Clone this repository.
3. Install pipenv: `pip install pipenv`
4. Install required packages from Pipfile: `pipenv install` from project root
5. Copy the `example.env` file and call the new file `.env`

Alternatively, you can skip installing pipenv and install the packages from requirements.txt.
Run `python -m src` to launch the app.

### 2. Create a Notion Integration

1. Create a new Notion integration: <https://www.notion.so/my-integrations/>
2. Add the Notion API key to the `.env` file
3. Add the integration to the desired Notion pages (in Page Settings > Connect To). Child pages inherit this setting.

### 3. Add OpenAI Keys

1. Create OpenAI API Keys at <https://platform.openai.com>
2. Add the API org and key to the `.env` file

### 4. Create a Slack App

1. Create a new Slack App.
2. Use the app manifest from the file `resources/slack_app_manifest.yaml` for the app configuration.
3. Add the app token and signing secret to the `.env` file

To chat with the app from Slack (rather than from the CLI) you should also follow these steps:

1. Change `self.interface` in `src/config.py` to `'slack'`.
2. Install ngrok to expose a public url: `brew install ngrok/ngrok/ngrok`
3. Start a local tunnel to expose the chatbot: `ngrok http 8000`
4. Run the app (see below).
5. Replace 'your-domain-here' with the ngrok url. You do this in the app manifest of the "Event Subscriptions" tab.

### 5. Run the App

To run the app you can run `pipenv run main` or `python -m src` from the project root.

### Changing the Config
To change the configuration of the chatbot, change the attributes of the Config class in `src/config.py`.


# To-Do

- Containerize the app.
- Separate the script that scrapes data from the chatbot script using Docker compose.
- Add logging.
- Add documentation (docstrings etc.).
- Include instructions on how to run and expose the app on common cloud providers.
- Save fetched documents in the cloud. They currently save locally.
- Dynamically set which integrations to use from environment variables.
- Improve Notion page retrieval. Not all Notion block types are supported now.
- Improve Slack conversation retrieval. Currently, each message is a separate document (including replies).
- Add integrations with more knowledge bases (e.g. Github, Hubspot).
