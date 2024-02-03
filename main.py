from datetime import datetime

import discord
from discord.ext import commands

import settings
from models import Message
from prompts import prompt

logger = settings.logging.getLogger("bot")

listening = False
messages: list[Message] = []

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
      listening = True
      logger.info(f"Listening to messages on channel {ctx.channel.name} "
                f"from {datetime.now().strftime('%m-%d-%Y %H:%M:%S')}")
      await ctx.send('Listening to your messages now.')

  @bot.command(
    aliases=['s']
  )
  async def stop(ctx):
      "Llama will stop listening to messages in this channel from now on."

      global listening
      listening = False
      logger.info(f"Stopped Listening to messages on channel "
              f"{ctx.channel.name} from {datetime.now().strftime('%m-%d-%Y')}")
      await ctx.send('Stopped listening to messages.')

  @bot.command(
    aliases=['f']
  )
  async def forget(ctx):
      "Llama will forget everything it remembered. It will forget all messages, todo, reminders etc."

      forget_all()
      await ctx.send('All messages forgotten.')

  @bot.command(
    aliases=['l']
  )
  async def llama(ctx, *query):
      "Llama will answer your query"

      global listening
    
      if not listening:
        await ctx.send(
          "I'm not listening to what y'all saying 🙈🙉🙊. "
          "\nRun \"/listen\" if you want me to start listening."
        )
        return

      if len(query) == 0:
        await ctx.send("What?")
        return
      await ctx.send(answer_query(" ".join(query), ctx))

  @bot.event
  async def on_message(message):
      global listening
      if message.author == bot.user:
          return

      if listening:
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
    messages.append(Message(
      is_in_thread=str(message.channel.type) == 'public_thread',
      posted_at=when,
      author=str(who),
      message_str=\
        f"[{when.strftime('%m-%d-%Y %H:%M:%S')}] - @{who} on #{message.channel}: `{msg_content}`",
      channel_id=message.channel.id
    ))

  def answer_query(query, ctx):
    thread_id = ctx.channel.id
    thread_messages = [
      msg.message_str for msg in messages if msg.channel_id==thread_id
    ][:5]
    partially_formatted_prompt = prompt.format(
      replies="\n".join(thread_messages),
      user_asking=str(ctx.author),
    )
    # print(partially_formatted_prompt)
    for msg in messages:
      print(msg)
      print()

    return f"Got query \"{query}\". Answering in a bit..."


  def forget_all():
      # Implement your logic here
      pass

  bot.run(settings.DISCORD_API_SECRET, root_logger=True)


if __name__ == "__main__":
    run()
