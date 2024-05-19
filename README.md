# Slack RAG Chatbot

Search through your Slack Pages and Notion Pages using a natural language interface.

This repository integrates with Notion's and Slack's APIs to pull Slack messages and Notion pages.
The chatbot has access to these documents and answers questions using RAG (retrieval-augment-generation).

The chatbot can be accessed from two interfaces: the CLI or Slack.

# Set-Up

### 1. Install the Repo

1. Install Python >= 3.8.
2. Clone this repository.
3. Install packages: `pip install -r requirements.txt`
4. Rename `example.env` to `.env` and add your keys to this file.

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

1. Create a new Slack App: <https://api.slack.com/apps>.
2. Use the app manifest from the file `resources/slack_app_manifest.yaml`.
3. Add the app token and signing secret to the `.env` file

To chat with the app from Slack (rather than from the CLI) you should also follow these steps:

1. Change `self.interface` in `src/config.py` to `'slack'`.
2. Install ngrok to expose a public url: `brew install ngrok/ngrok/ngrok`
3. Start a local tunnel to expose the chatbot: `ngrok http 8000`
4. Run the app (see below).
5. Replace 'your-domain-here' with the ngrok url. You do this in the app manifest of the "Event Subscriptions" tab.

### 5. Run the App

Run the command `python -m src` from the project root.

### Changing the Config
To change the configuration of the chatbot, change the attributes of the Config class in `src/config.py`.


# To-Do

Unordered:
- Integrate more knowledge bases (e.g. Github, Hubspot).
- Add more LLM options.
- A UI to manage integrations.
- Containerize the app.
- Separate data scraping into a separate service.
- Include instructions to run on common cloud providers.
- Add logging.
- Add documentation (docstrings etc.).
- Save fetched documents in cloud storage. They are currently saved locally.
- Determine integrations to use from environment variables.
- Use environ package for config.
- Support more Notion block types.
- Improve conversion of Slack messages to documents. Currently, each message is a separate document (with replies).
- Store conversations in a database.