## LlamaBot

An open-source Discord bot, created using LlamaIndex, that -
- Listens to your server conversations
- Continuously learns from them
- Answers your questions from the entire server.

https://github.com/rsrohan99/llamabot/assets/62835870/eaab6db1-8f79-4e3a-aaf0-c132b966d9f6

It’s recommended to host this bot yourself for your server, but if you wanna try out first, you can invite the bot to your server through [this link](https://discord.com/api/oauth2/authorize?client_id=1203216926730616862&permissions=3072&scope=bot).

Tech stack used for this bot:
1. **LlamaIndex** as the RAG framework
2. **Google Gemini** Pro as the LLm and Embedding model
3. **Qdrant cloud** as the vectorstore
4. **discord.py** to setup the bot logic
5. Finally deploy it to **Replit**

Checkout [my blog post](https://clusteredbytes.pages.dev/posts/2024/create-a-discord-chatbot-using-llamaindex-for-your-server/) where I walk you through the entire process of building a full-fledged discord bot like this using LlamaIndex.

### Features

- `/llama` - Ask LlamaBot questions
- `/listen` - Starts listening to messages across the server and remembers those.
- `/stop` - Stops listening to messages
- `/forget` - Forgets all messages from the server
- `/status` - Shows whether bot is listening to messages or not


### Installation

```bash
$ git clone https://github.com/rsrohan99/llamabot.git

$ cd llamabot
```

Now set the following Environment variables:
```bash
DISCORD_API_TOKEN='...'

QDRANT_KEY='...'
QDRANT_URL='...'

GOOGLE_API_KEY='...'

# USE_OPENAI=true  # set this to use gpt4, add OPENAI_API_KEY as well, set USE_OPENAI to '' to use Gemini Pro
# OPENAI_API_KEY='...'
```
If you wanna use GPT-4 with Ada embeddings, then set `USE_OPENAI` to `true` and add `OPENAI_API_KEY`

Next run the program:

```bash
$ poetry install

$ poetry run python llamabot.py
```
