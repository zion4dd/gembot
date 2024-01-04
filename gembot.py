import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters


load_dotenv()
TOKEN = os.getenv('GEMINI_CHAT_TOKEN')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')


def ask_gemini(ask):
    print(ask)
    response = model.generate_content(ask)
    return response.text

async def start(update, context):
    msg = '''здарова. это гугл чат бот. самый настоящий. только с амнезией.
    я умею давать ответ только на один запрос. предыдущий диалог не запоминаю.
    поэтому тщательно формулируй запрос.
    может быть в будущем я смогу вести диалог, но пока мне лень.
    чего изволите?'''
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                             text=msg)

async def echo(update, context):
    res = ask_gemini(update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                             text=res)


if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT, echo))
    app.run_polling()

