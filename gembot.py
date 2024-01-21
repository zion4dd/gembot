# https://ai.google.dev/tutorials/python_quickstart

import os
import logging
import requests
import time

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from bs4 import BeautifulSoup


# function to use
MODE = 'proxy'  # gemini | proxy
HTTPS_FILENAME = 'https.txt'

# .env
load_dotenv()
TOKEN = os.getenv('GEMINI_CHAT_TOKEN')
API_KEY = os.getenv("GOOGLE_API_KEY")
MAX = int(os.getenv("MAX", 20))  # max proxies from list
TIMEOUT = int(os.getenv("TIMEOUT", 20))  # seconds
LIFETIME = int(os.getenv("LIFETIME", 600))  # seconds

# logging
logging.basicConfig(
    filename="logfile",
    format="[%(asctime)s] func: %(funcName)s()\n%(message)s",
    datefmt="%Y-%m-%d %H:%M",
    level=logging.WARNING,
    encoding="UTF-8",
)

# ask_gem_proxy()
if MODE == 'proxy':
    url_https = 'https://www.sslproxies.org/'
    url_gemini = "https://generativelanguage.googleapis.com/v1/models/gemini-pro:generateContent"
    headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": API_KEY,
                }

# ask_gem()
if MODE == 'gemini':
    import google.generativeai as genai
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-pro')


def ask_gem(ask):
    try:
        response = model.generate_content(ask)
        logging.warning('ASK: %s' % ask)
        logging.warning('RESP: %s' % response.text)
        return response.text
    
    except Exception as e:
        logging.error(str(e))
        return f"Exception: {e}"
    

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
    return lifetime


def get_https_list():
    lifetime = check_https_file_ctime()
    if lifetime > LIFETIME:
        get_https_file()
    try:
        with open(HTTPS_FILENAME, 'r') as f:
            https_list = f.readlines()[:MAX]
        return https_list
    
    except FileNotFoundError as e:
        logging.error(str(e))


def write_https_list(https_list: list):
    try:
        with open(HTTPS_FILENAME, 'w') as f:
            f.writelines(https_list)

    except IOError as e:
        logging.error(str(e))


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
            # logger.warning(str(e))
            https_list.pop(0)
            continue
    
    get_https_file()
    return 'Халявные прокси не отвечают.\nПерегрузил список.\nПопробуй еще раз.'


async def start(update, context):
    msg = 'start ok'
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=msg)


async def get_https(update, context):
    res = get_https_file()
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

async def get_lifetime(update, context):
    lifetime = check_https_file_ctime()
    res = 'lifetime: %s' % lifetime
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

async def get_country(update, context):
    url = 'https://2ip.ru'
    https = get_https_list()[0]
    proxies = {'https': https.strip()}
    response = requests.get(url, proxies=proxies)
    soup = BeautifulSoup(response.text, 'html.parser')

    ip = soup.find('div', class_='ip').text.strip()
    country = soup.find('div', class_='value-country').text.strip().split('\n')[0]
    
    res = f"{ip} - {country}"
    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)


async def echo(update, context):
    res = 'MODE is None'
    if MODE == 'gemini':
        res = ask_gem(update.message.text)
    if MODE == 'proxy':
        res = ask_gem_proxy(update.message.text)

    await context.bot.send_message(chat_id=update.effective_chat.id, 
                                    text=res)
    

if __name__ == "__main__":
    get_https_file()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('getproxy', get_https))
    app.add_handler(CommandHandler('ctime', get_lifetime))
    app.add_handler(CommandHandler('country', get_country))
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
