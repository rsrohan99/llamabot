from llama_index.prompts import PromptTemplate

prompt_template = (
  "Your context is a series of discord chat messages. Each chat message is in this format: [when the message was posted] - @user_who_posted on #[channel_where_message_was_posted]: `message_content`\n"
  "There can be up to 20 chat messages.\n"
  "The messages are sorted by recency, so the most recent one is first in the list.\n"
  "The most recent messages should take precedence over older ones.\n"
  "---------------------\n"
  "{context_str}"
  "\n---------------------\n"
  "You are a helpful AI assistant who has been listening to everything everyone has been saying. Your username is @{bot_name} \n"
  "Now @{user_asking} is asking a question that you'll answer correctly, using the most recent and relevant information from above."
  "\nFor additional context, here are the last few chat messages before @{user_asking} asked their query:"
  "\n-------------------"
  "\n{replies}"
  "\n-------------------"
  "\nGiven the most relevant chat messages above, please answer this question, which was asked by \"@{user_asking}\": `{query_str}`"
  "\nYour helpful response: "
)

prompt = PromptTemplate(prompt_template)
