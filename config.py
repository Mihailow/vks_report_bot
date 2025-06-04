from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand, BotCommandScopeDefault

from apscheduler.schedulers.asyncio import AsyncIOScheduler

DB_HOST = "localhost"
DB_NAME = "vks_main"
DB_USER = "postgres"
DB_PASS = "postgres"

telegram_token = "6353026522:AAG00eY0ErQEKJwacUPkgjB85X_1d6w3zWs"
is_testing = True
# from_email = "mihailbramnik@yandex.ru"
# from_email_password = "jqukfyyvtjzutkow"
dest_email = "mike-bramnik@yandex.ru"

# telegram_token = "6363900608:AAFDltNwtWq4KQKxG5uzf1ZoeRuBavmgrkM"
# is_testing = False
from_email = "vks.olga@yandex.ru"
from_email_password = "kznofsnmcnctgjye"
# dest_email = "buh@vksproect.ru"

subject = "Платёж по счёту"

bot = Bot(token=telegram_token)
dp = Dispatcher(bot, storage=MemoryStorage())
scheduler = AsyncIOScheduler()

last_message = {}
