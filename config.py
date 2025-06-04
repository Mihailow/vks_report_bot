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

telegram_token = "6353026522:AAH6nwB6AgNQKQaUwT9PFvfI-8vA7NuYwlY"
is_testing = True

# telegram_token = '7150536489:AAGh1JMsV5Rh_Y5lgf4wUlSd9kQUFVVk23I'
# is_testing = False

bot = Bot(token=telegram_token)
dp = Dispatcher(bot, storage=MemoryStorage())
scheduler = AsyncIOScheduler()

last_message = {}
last_messages = {}
