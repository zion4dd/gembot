import os
import google.generativeai as genai
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# import logging

# def logger(name):
#     "logger.[debug | info | warning | error | critical]"
#     logger = logging.getLogger(name)
#     logger.setLevel(20)
#     formatter = logging.Formatter(f"[%(asctime)s] func: %(funcName)s()\n%(message)s", 
#                                   datefmt="%Y-%m-%d %H:%M")
#     f_handler = logging.FileHandler(f"./log/{name}.log")
#     s_handler = logging.StreamHandler()
#     f_handler.setFormatter(formatter)
#     logger.addHandler(f_handler)
#     logger.addHandler(s_handler)
#     return logger

load_dotenv()
TOKEN = os.getenv('GEMINI_CHAT_TOKEN')
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))
model = genai.GenerativeModel('gemini-pro')


def ask_gemini(ask):
    try:
        response = model.generate_content(ask)
        return response.text
    except Exception as e:
        return e


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

