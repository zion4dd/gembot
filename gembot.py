# https://ai.google.dev/tutorials/python_quickstart

import os
import logging
import requests
import google.generativeai as genai

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
# from proxies import proxies

from zenrows import ZenRowsClient
import json

logger = logging.getLogger()
logger.setLevel(30)
formatter = logging.Formatter(f"[%(asctime)s] func: %(funcName)s()\n%(message)s", 
                                datefmt="%Y-%m-%d %H:%M")
f_handler = logging.FileHandler(f"logfile.log")
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)


load_dotenv()
TOKEN = os.getenv('GEMINI_CHAT_TOKEN')
API_KEY = os.getenv("GOOGLE_API_KEY")

genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

url = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
            }

zenclient = ZenRowsClient('6b88609186d21ab8d8a723f7daec145606c80771')


def ask_gemini(ask):
    try:
        response = model.generate_content(ask)
        logger.warning('ASK: %s' % ask)
        logger.warning('RESP: %s' % response.text)
        return response.text
    
    except Exception as e:
        logger.error(str(e))
        return f"Exception: {e}"
    

def ask_gemini_2(ask):
    data = {"contents":[{"parts":[{"text": ask}]}]}
    https_list = open("https.txt", "r").read().strip().split("\n")[:20]
    while https_list:
        proxies = {
                'https': https_list.pop(0)
            }
        try:
            response = requests.post(url, headers=headers, json=data, proxies=proxies).json()
            logger.warning(">>> GOOD: %s" % proxies['https'])
            return response.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text")
        except Exception as e:
            logger.warning(str(e))
            continue
    return 'list empty'


def ask_gemini_zen(ask):
    data = {"contents":[{"parts":[{"text": ask}]}]}
    params = {
    "js_render": "true",
    "json_response": "true",
    "premium_proxy": "true",
    }
    j = json.dumps(data)
    response = zenclient.post(url, headers=headers, data=j, params=params)
    content_text = json.loads(response.text)
    content_text = content_text.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text")
    return content_text


async def start(update, context):
#     msg = '''здарова. это гугл чат бот. самый настоящий. только с амнезией.
# я умею давать ответ только на один запрос. предыдущий диалог не запоминаю.
# поэтому тщательно формулируй запрос.
# может быть в будущем я смогу вести диалог, но пока мне лень.
# чего изволите?'''
    msg = 'start ok'
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                             text=msg)


async def echo(update, context):
    res = ask_gemini_2(update.message.text)
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                             text=res)
    

if __name__ == "__main__":
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.TEXT, echo))
    app.run_polling()

