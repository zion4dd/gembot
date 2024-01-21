# https://ai.google.dev/tutorials/python_quickstart

import os
import logging
import requests
import redis
import json
import lxml

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bs4 import BeautifulSoup


# .env
load_dotenv()
PROXY = bool(os.getenv('PROXY'))
TOKEN = os.getenv('GEMINI_CHAT_TOKEN')
API_KEY = os.getenv("GOOGLE_API_KEY")
MAX = int(os.getenv("MAX", 20))  # max proxies from list
TIMEOUT = int(os.getenv("TIMEOUT", 20))  # seconds
LIFETIME = int(os.getenv("LIFETIME", 600))  # seconds
LOGLEVEL = int(os.getenv("LOGLEVEL", 30))


# logging
logging.basicConfig(
    filename="logfile",
    format="[%(asctime)s] func: %(funcName)s()\n%(message)s",
    datefmt="%Y-%m-%d %H:%M",
    level=LOGLEVEL,
    encoding="UTF-8",
)


PARSER = 'lxml'  # lxml | html.parser
r_key = 'https_list'
r = redis.Redis(host='localhost', port=6379, decode_responses=True)


if PROXY:
    url_https = 'https://www.sslproxies.org/'
    url_gemini = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": API_KEY,
                }
else:
    import google.generativeai as genai
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')


def ask_gem(ask):
    try:
        response = model.generate_content(ask)
        logging.debug('ASK: %s' % ask)
        logging.debug('RESP: %s' % response.text)
        return response.text
    
    except Exception as e:
        logging.error(str(e))
        return f"Exception: {e}"
    

def get_https() -> str:
    try:
        src = requests.get(url_https)
        soup = BeautifulSoup(src.text, PARSER)
        https_str: str = soup.find(attrs={'class':'modal-body'}).find(attrs={'class':'form-control'}).text

        separator = ('\n\n')
        index: int = https_str.find(separator) + len(separator)
        https_str: str = https_str[index:]
        https_list = https_str.split('\n')[:MAX]
        set_https_list(https_list)
        return https_str[:100] + '...'
    
    except Exception as e:
        logging.error('Error: getting https from %s failed.' % url_https)
        return str(e)
    

def get_https_list() -> list:
    for _ in range(3):
        https_list = r.get(r_key)
        if https_list:
            return json.loads(https_list)
            return https_list.split('\n')
        
        get_https()


def set_https_list(https_list: list):
    https_str = json.dumps(https_list)
    # https_str = '\n'.join(https_list)
    r.set(r_key, https_str, ex=LIFETIME)


def ask_gem_proxy(ask):
    data = {"contents":[{"parts":[{"text": ask}]}]}
    https_list = get_https_list()
    if https_list is None:
        return 'Не удалось загрузить халявные прокси.'
    
    original = https_list.copy()

    while https_list:
        https = https_list[0]
        proxies = {'https': https.strip()}
        try:
            response = requests.post(url_gemini, headers=headers, json=data, proxies=proxies, timeout=TIMEOUT)
            if response.status_code == 400:
                raise Exception('Exception: 400 User location is not supported for the API use.')
            
            if https_list != original:
                set_https_list(https_list)

            response = response.json()
            return response.get("candidates", [])[0].get("content", {}).get("parts", [])[0].get("text")
        
        except Exception as e:
            # logger.warning(str(e))
            https_list.pop(0)
            continue
    
    get_https()
    return 'Халявные прокси не отвечают.\nПерегрузил список.\nПопробуй еще раз.'


async def start(update, context):
    msg = 'start ok'
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=msg)


async def run_get_https(update, context):
    res = get_https()
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

async def get_redis(update, context):
    lifetime = r.ttl(r_key)
    https = r.get(r_key)
    res = 'lifetime: %s\nhttps:\n%s' % (lifetime, https[:100] + '...')
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

async def get_country(update, context):
    url = 'https://2ip.ru'
    https = get_https_list()
    if https is None:
        res = 'Не удалось загрузить халявные прокси.'
    else:
        ip = https[0]
        proxies = {'https': ip.strip()}
        try:
            response = requests.get(url, proxies=proxies)
            soup = BeautifulSoup(response.text, PARSER)

            ip = soup.find('div', class_='ip').text.strip()
            country = soup.find('div', class_='value-country').text.strip().split('\n')[0]
            
            res = f"{ip} - {country}"

        except Exception as e:
            res = ip + '\n' + str(e)

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

async def unknown(update, context):
    res = 'unknown command'
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)


async def echo(update, context):
    if PROXY:
        res = ask_gem_proxy(update.message.text)
    else:
        res = ask_gem(update.message.text)

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

if __name__ == "__main__":
    get_https()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('getproxy', run_get_https))
    app.add_handler(CommandHandler('redis', get_redis))
    app.add_handler(CommandHandler('country', get_country))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))
    app.add_handler(MessageHandler(filters.TEXT, echo))
    app.run_polling()



#     msg = '''здарова. это гугл чат бот. самый настоящий. только с амнезией.
# я умею давать ответ только на один запрос. предыдущий диалог не запоминаю.
# поэтому тщательно формулируй запрос.
# может быть в будущем я смогу вести диалог, но пока мне лень.
# еще я испльзую халявные прокси, потому что гугл нас забанил. поэтому туплю.
# '''
    

# from logging import handlers
# logger = logging.getLogger()
# logger.setLevel(logging.WARNING)
# formatter = logging.Formatter(f"[%(asctime)s] func: %(funcName)s()\n%(message)s", 
#                                 datefmt="%Y-%m-%d %H:%M")
# f_handler = handlers.RotatingFileHandler(filename='logfile', 
                                        #  maxBytes=1000, 
                                        #  backupCount=1, 
                                        #  encoding="UTF-8", 
                                        #  )
# f_handler.setFormatter(formatter)
# logger.addHandler(f_handler)
