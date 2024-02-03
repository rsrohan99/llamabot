from datetime import datetime
from pathlib import Path
import pickle

import discord
from discord.ext import commands

from llama_index.llms import OpenAI
from llama_index import VectorStoreIndex, StorageContext, ServiceContext
from llama_index.postprocessor import FixedRecencyPostprocessor
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.schema import TextNode, NodeRelationship, RelatedNodeInfo
from llama_index.vector_stores.types import (
    MetadataFilter,
    MetadataFilters,
    FilterOperator,
)

import qdrant_client

import settings
from models import Message
from prompts import prompt

logger = settings.logging.getLogger("bot")

persist_dir = "./persist"

messages_path = Path(persist_dir + "/messages.pkl")
listening_path = Path(persist_dir + "/listening.pkl")

messages_path.parent.mkdir(parents=True, exist_ok=True)

if messages_path.is_file():
  with open(messages_path, 'rb') as file:
    messages = pickle.load(file)
else:
  messages_path.touch(exist_ok=True)
  messages: dict[int, list[Message]] = {} 

if listening_path.is_file():
  with open(listening_path, 'rb') as file:
    listening = pickle.load(file)
else:
  listening_path.touch(exist_ok=True)
  listening: dict[int, bool] = {}

# initialize qdrant client
qd_client = qdrant_client.QdrantClient(
  url=settings.QDRANT_URL,
  api_key=settings.QDRANT_API_KEY
)

qd_collection = 'discord_llamabot'

vector_store = QdrantVectorStore(client=qd_client,
                                 collection_name=qd_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

index = VectorStoreIndex([],storage_context=storage_context)

def persist_listening():
  global listening

  print(listening)
  with open(listening_path, 'wb') as file:
    pickle.dump(listening, file)

def persist_messages():
  global messages

  print(messages)
  with open(messages_path, 'wb') as file:
    pickle.dump(messages, file)

persist_messages()
persist_listening()

def run():
  "Run LlamaBot."
  intents = discord.Intents.default()
  intents.message_content = True

  bot = commands.Bot(
    command_prefix='/',
    intents=intents
  )


  @bot.event
  async def on_ready():
    logger.info(f"User: {bot.user} (ID: {bot.user.id})")

  @bot.command(
    aliases=['li']
  )
  async def listen(ctx):
      "Llama will start listening to messages in this channel from now on."

      global listening
      listening[ctx.guild.id] = True
      persist_listening()
      logger.info(f"Listening to messages on channel {ctx.channel.name} of server: {ctx.guild.id} "
                f"from {datetime.now().strftime('%m-%d-%Y %H:%M:%S')}")
      await ctx.send('Listening to your messages now.')

  @bot.command(
    aliases=['s']
  )
  async def stop(ctx):
      "Llama will stop listening to messages in this channel from now on."

      global listening
      listening[ctx.guild.id] = False
      persist_listening()
      logger.info(f"Stopped Listening to messages on channel "
              f"{ctx.channel.name} from {datetime.now().strftime('%m-%d-%Y')}")
      await ctx.send('Stopped listening to messages.')

  @bot.command(
    aliases=['f']
  )
  async def forget(ctx):
      "Llama will forget everything it remembered. It will forget all messages, todo, reminders etc."

      forget_all(ctx)
      await ctx.send('All messages forgotten.')

  @bot.command(
    aliases=['l']
  )
  async def llama(ctx, *query):
      "Llama will answer your query"

      global listening
    
      if not listening.get(ctx.guild.id, False):
        await ctx.send(
          "I'm not listening to what y'all saying 🙈🙉🙊. "
          "\nRun \"/listen\" if you want me to start listening."
        )
        return

      if len(query) == 0:
        await ctx.send("What?")
        return
      await ctx.send(answer_query(" ".join(query), ctx, bot))

  @bot.event
  async def on_message(message):
      global listening
      if message.author == bot.user:
          return

      if listening.get(message.guild.id, False):
        if not message.content.startswith('/'):
            # Call the remember_message function here
            remember_message(message)

      await bot.process_commands(message)

  def remember_message(message):
    when = message.created_at
    who=message.author
    msg_content = message.content

    logger.info(
    f"Remembering new message \"{msg_content}\" from {who} on channel "
    f"{message.channel.name} at {datetime.now().strftime('%m-%d-%Y %H:%M:%S')}"
    )

    node = TextNode(
      text=f"[{when.strftime('%m-%d-%Y %H:%M:%S')}] - @{who} on #{message.channel}: `{msg_content}`",
      metadata={
        'author': str(who),
        'posted_at': str(when),
        'channel_id': message.channel.id,
        'guild_id': message.guild.id
      },
      excluded_llm_metadata_keys=['author', 'posted_at', 'channel_id', 'guild_id'],
      excluded_embed_metadata_keys=['author', 'posted_at', 'channel_id', 'guild_id'],
    )

    index.insert_nodes([node])

    if not messages.get(message.guild.id, None):
      messages[message.guild.id] = []
    messages[message.guild.id].append(Message(
      is_in_thread=str(message.channel.type) == 'public_thread',
      posted_at=when,
      author=str(who),
      message_str=f"[{when.strftime('%m-%d-%Y %H:%M:%S')}] - @{who} on #{message.channel}: `{msg_content}`",
      channel_id=message.channel.id
    ))
    persist_messages()

  def answer_query(query, ctx, bot):
    channel_id = ctx.channel.id
    thread_messages = [
      msg.message_str for msg in messages.get(ctx.guild.id, []) if msg.channel_id==channel_id
    ][:5]
    partially_formatted_prompt = prompt.partial_format(
      replies="\n".join(thread_messages),
      user_asking=str(ctx.author),
      bot_name=str(bot.user)
    )
    # print(partially_formatted_prompt)
    # for msg in messages:
    #   print(msg)
    #   print()
    filters = MetadataFilters(
      filters=[
        MetadataFilter(
          key="guild_id", operator=FilterOperator.EQ, value=ctx.guild.id
        ),
    ]
)
    
    llm = OpenAI()
    service_context = ServiceContext.from_defaults(
      llm=llm
    )
    postprocessor = FixedRecencyPostprocessor(
        top_k=20, 
        date_key="posted_at", # the key in the metadata to find the date
        service_context=service_context
    )
    query_engine = index.as_query_engine(
      verbose=True,
      filters=filters,
      similarity_top_k=20,
      node_postprocessors=[postprocessor])
    query_engine.update_prompts(
        {"response_synthesizer:text_qa_template": partially_formatted_prompt}
    )

    # return f"Got query \"{query}\". Answering in a bit..."
    return query_engine.query(query)


  def forget_all(ctx):
    from qdrant_client.http import models as rest

    global qd_client

    messages.pop(ctx.guild.id)
    persist_messages()


    qd_client.delete(
        collection_name=qd_collection,
        points_selector=rest.Filter(
            must=[
                rest.FieldCondition(
                    key="guild_id", match=rest.MatchValue(value=ctx.guild_id)
                )
            ]
        ),
    )


  bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
