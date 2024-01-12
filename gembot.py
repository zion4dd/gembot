# https://ai.google.dev/tutorials/python_quickstart

import os
import logging
import requests
import time
import google.generativeai as genai

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bs4 import BeautifulSoup

from zenrows import ZenRowsClient
import json


# function to use
MODE = 'proxy'  # gemini | proxy | zenrows
HTTPS_FILENAME = 'https.txt'

# .env
load_dotenv()
TOKEN = os.getenv('GEMINI_CHAT_TOKEN')
API_KEY = os.getenv("GOOGLE_API_KEY")
MAX = int(os.getenv("MAX", 20))
TIMEOUT = int(os.getenv("TIMEOUT", 20))  # seconds
LIFETIME = int(os.getenv("LIFETIME", 600))  # seconds

# logger
logger = logging.getLogger()
logger.setLevel(30)
formatter = logging.Formatter(f"[%(asctime)s] func: %(funcName)s()\n%(message)s", 
                                datefmt="%Y-%m-%d %H:%M")
f_handler = logging.FileHandler(f"logfile.log")
f_handler.setFormatter(formatter)
logger.addHandler(f_handler)


url_https = 'https://www.sslproxies.org/'
url_gemini = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": API_KEY,
            }

# ask_gem()
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

# ask_gem_zen()
zenclient = ZenRowsClient('6b88609186d21ab8d8a723f7daec145606c80771')


def get_https_file():
    try:
        src = requests.get(url_https)
        soup = BeautifulSoup(src.text, 'html.parser')
        https_str: str = soup.find(attrs={'class':'modal-body'}).find(attrs={'class':'form-control'}).text

        separator = ('\n\n')
        index: int = https_str.find(separator) + len(separator)
        https_str: str = https_str[index:]

        with open(HTTPS_FILENAME, 'w') as f:
            f.write(https_str)
        # os.chmod(HTTPS_FILENAME, mode=0o777)
        return https_str[:50]
    
    except Exception as e:
        return str(e)
    

def check_https_file_ctime():
    ctime = os.path.getctime(HTTPS_FILENAME)
    lifetime = time.time() - ctime
    if lifetime > LIFETIME:
        get_https_file()
    return 'lifetime: ' + str(lifetime)


def get_https_list():
    check_https_file_ctime()
    try:
        with open(HTTPS_FILENAME, 'r') as f:
            https_list = f.readlines()[:MAX]
        return https_list
    
    except FileNotFoundError as e:
        logger.error(str(e))


def write_https_list(https_list):
    try:
        with open(HTTPS_FILENAME, 'w') as f:
            f.writelines(https_list)

    except IOError as e:
        logger.error(str(e))


def ask_gem(ask):
    try:
        response = model.generate_content(ask)
        logger.warning('ASK: %s' % ask)
        logger.warning('RESP: %s' % response.text)
        return response.text
    
    except Exception as e:
        logger.error(str(e))
        return f"Exception: {e}"
    

def ask_gem_proxy(ask):
    # https_list = open("https.txt", "r").read().strip().split("\n")[:20]
    data = {"contents":[{"parts":[{"text": ask}]}]}
    https_list = get_https_list()
    original = https_list.copy()

    while https_list:
        https = https_list[0]
        proxies = {'https': https.strip()}
        try:
            response = requests.post(url_gemini, headers=headers, json=data, proxies=proxies, timeout=TIMEOUT)
            if response.status_code == 400:
                raise Exception('Exception: 400 User location is not supported for the API use.')
            
            if https_list != original:
                write_https_list(https_list)

            response = response.json()
            return response.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text")
        
        except Exception as e:
            logger.warning(str(e))
            https_list.pop(0)
            continue
    
    get_https_file()
    return 'Халявные прокси не отвечают.\nПерегрузил список.\nПопробуй еще раз.'


def ask_gem_zen(ask):
    data = {"contents":[{"parts":[{"text": ask}]}]}
    params = {
    "js_render": "true",
    "json_response": "true",
    "premium_proxy": "true",
    }
    j = json.dumps(data)
    response = zenclient.post(url_gemini, headers=headers, data=j, params=params)
    content_text = json.loads(response.text)
    content_text = content_text.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text")
    return content_text


async def start(update, context):
    msg = '''здарова. это гугл чат бот. самый настоящий. только с амнезией.
я умею давать ответ только на один запрос. предыдущий диалог не запоминаю.
поэтому тщательно формулируй запрос.
может быть в будущем я смогу вести диалог, но пока мне лень.
еще я испльзую халявные прокси, потому что гугл нас забанил. поэтому туплю.
чего изволите?'''
    # msg = 'start ok'
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=msg)


async def get_https(update, context):
    res = get_https_file()
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

async def get_lifetime(update, context):
    res = check_https_file_ctime()
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)


async def echo(update, context):
    res = 'MODE is None'
    if MODE == 'gemini':
        res = ask_gem(update.message.text)
    if MODE == 'proxy':
        res = ask_gem_proxy(update.message.text)
    if MODE == 'zenrows':
        res = ask_gem_zen(update.message.text)

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

if __name__ == "__main__":
    get_https_file()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('get', get_https))
    app.add_handler(CommandHandler('ctime', get_lifetime))
    app.add_handler(MessageHandler(filters.TEXT, echo))
    app.run_polling()

