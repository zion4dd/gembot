## Telegram чат-бот Gemini от Google.

https://t.me/GoogleZiBot

Диалог не запоминает.  
Работает в качестве справочника ответ-запрос.  
Парсит бесплатные прокси с сайта https://www.sslproxies.org/,  
что позволяет ему работать в странах, где Gemini не отвечает.  
Список прокси подгружает в Redis.

### Команды бота:

/start - старт бота  
/getproxy - обновить прокси  
/redis - список прокси в редисе (живут 10 минут - параметр LIFETIME)  
/country - адрес и страна последнего рабочего прокси

### Параметры:

PROXY = использовать прокси True | False  
TOKEN = токен Telegram бота  
API_KEY = Gemini API key  
MAX = колиство прокси из списка с сайта https://www.sslproxies.org/  
TIMEOUT = время ожидания ответа через каждый прокси в секундах  
LIFETIME = время жизни списка прокси в Redis (потом список обновляется)  
LOGLEVEL = уровень логирования

```
# .env

PROXY=true
LOGLEVEL=30
MAX=20
TIMEOUT=30
LIFETIME=600
GOOGLE_API_KEY=AI********
GEMINI_CHAT_TOKEN=6556007355:AAHx************
```
