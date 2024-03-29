import os
import logging

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from config import *
from keyboards import *
from postgres import *


class Status(StatesGroup):
    user_add_document = State()
    user_add_company = State()
    user_add_facility = State()
    user_add_document_number = State()
    user_add_amount = State()
    user_add_date = State()
    user_add_purpose = State()
    user_add_type = State()
    user_add_upd_type = State()

    user_document_registry = State()

    admin_document_registry = State()


class CheckBotStatusMiddleware(BaseMiddleware):
    async def on_pre_process_message(self, message: types.Message, data: dict):
        await bot.delete_message(message.from_user.id, message.message_id)
        await self.before_any_process(message.from_user.id, message.message_id, message.text)
        logging.info(f"\n   Пользователь: {message.from_user.id} прислал сообщение\n"
                     f"   Id сообщения: {message.message_id}\n"
                     f"   Текст сообщения: {message.text}\n"
                     f"   Тип сообщения: {message.content_type}")

    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        await callback_query.answer()
        logging.info(f"\n   Пользователь: {callback_query.from_user.id} нажал кнопку\n"
                     f"   Id сообщения: {callback_query.message.message_id}\n"
                     f"   Текст сообщения: {callback_query.message.text}\n"
                     f"   Callback: {callback_query.data}")
        await self.before_any_process(callback_query.from_user.id, callback_query.message.message_id,
                                      call_data=callback_query.data)

    @staticmethod
    async def before_any_process(user_id, mes_id, mes_text=None, call_data=None):
        if user_id == 641825727 and is_testing is False:
            text = "Работаю!"
            await send_message(user_id, text)
        user = await get_user(user_id)
        if user is None:
            admin = await get_admin(user_id)
            if user is None and admin is None:
                is_password = None
                if mes_text:
                    is_password = await get_user_by_password(mes_text)
                if mes_text is None or is_password is None:
                    text = "Введите пароль"
                    await send_last_message(user_id, text)
                    raise CancelHandler()
                else:
                    await update_user_tg_id(user_id, mes_text)
                    text = "Здравствуйте!"
                    keyboard = await user_main_keyboard()
                    await send_message(user_id, text, keyboard)
                    raise CancelHandler()


middleware = CheckBotStatusMiddleware()
dp.middleware.setup(middleware)


async def send_message(chat_id, text, keyboard=None, document=None, reply=None):
    if document:
        try:
            document_file = open(str(document), "rb")
            mes = await bot.send_document(chat_id, document_file, caption=text, reply_markup=keyboard,
                                          reply_to_message_id=reply)
            logging.info(f"\n   Бот ответил пользователю {mes.chat.id}\n"
                         f"   Id сообщения: {mes.message_id}\n"
                         f"   Текст сообщения: {mes.text}\n")
            return mes
        except Exception as e:
            logging.error(f"send_message {chat_id}", exc_info=True)

    mes = await bot.send_message(chat_id, text=text, reply_markup=keyboard, reply_to_message_id=reply)
    logging.info(f"\n   Бот ответил пользователю {mes.chat.id}\n"
                 f"   Id сообщения: {mes.message_id}\n"
                 f"   Текст сообщения: {mes.text}\n")
    return mes


async def send_last_message(chat_id, text, keyboard=None):
    await delete_last_message(chat_id)
    mes = await send_message(chat_id, text, keyboard)
    last_message[chat_id] = mes.message_id
    return mes


async def delete_last_message(chat_id):
    if chat_id in last_message:
        try:
            await bot.delete_message(chat_id, last_message[chat_id])
            del (last_message[chat_id])
        except Exception as e:
            logging.error(f"delete_last_message {chat_id} {last_message[chat_id]}", exc_info=True)


async def send_last_messages(chat_id, text, keyboard=None):
    mes = await send_message(chat_id, text, keyboard)
    if chat_id not in last_messages or last_messages[chat_id] is None:
        last_messages[chat_id] = []
    last_messages[chat_id].append(mes.message_id)
    return mes


async def delete_last_messages(chat_id):
    if chat_id in last_messages:
        for message in last_messages[chat_id]:
            try:
                await bot.delete_message(chat_id, message)
            except Exception as e:
                logging.error(f"delete_last_message {chat_id} {last_messages[chat_id]}", exc_info=True)
        del (last_messages[chat_id])


async def change_message(chat_id, mes_id, text, keyboard=None, caption=False):
    try:
        if caption:
                mes = await bot.edit_message_caption(chat_id, mes_id, caption=text, reply_markup=keyboard)
                logging.info(f"\n   Бот меняет сообщение пользователя {mes.chat.id}\n"
                             f"   Id сообщения: {mes.message_id}\n"
                             f"   Текст сообщения: {mes.text}\n")

        else:
                mes = await bot.edit_message_text(text, chat_id, mes_id, reply_markup=keyboard)
                logging.info(f"\n   Бот меняет сообщение пользователя {mes.chat.id}\n"
                             f"   Id сообщения: {mes.message_id}\n"
                             f"   Текст сообщения: {mes.text}\n")
    except Exception as e:
        if e.args[0] == ("Message is not modified: specified new message content and reply "
                         "markup are exactly the same as a current content and reply markup of the message"):
            return
        else:
            logging.error(f"change_message", exc_info=True)


async def delete_document(data):
    if "document_name" in data:
        try:
            os.remove(data["document_name"])
        except Exception as e:
            logging.error(f"delete_document {data['document_name']}", exc_info=True)


async def add_report(data):
    admins = await get_admins()

    report_id = await insert_report(data)
    report = await get_report(report_id)
    text = f"Номер: {report['document_number']}\n"
    text += f"Компания: {report['company']}\n"
    text += f"Объект: {report['facility']}\n"
    text += f"Сумма: {report['amount']}\n"
    text += f"Дата: {report['date']}\n"
    text += f"Назначение: {report['purpose']}\n"
    text += f"Тип: {report['type']}"
    if report["upd_type"] is not None:
        text += f" {report['upd_type']}\n"
    else:
        text += "\n"
    if report["document_name"] is not None:
        mes = await send_message(data["user_id"], text, document=report["document_name"])
        file_id = mes.document.file_id
        await update_report_file_id(report["report_id"], file_id)
        text = f"ФИО: {report['creator']}\n" + text
        for admin in admins:
            await send_message(admin["tg_id"], text, document=report["document_name"])
    else:
        await send_message(data["user_id"], text)
        text = f"ФИО: {report['creator']}\n" + text
        for admin in admins:
            await send_message(admin["tg_id"], text)

    if report['type'] == "без чека" or report['upd_type'] == "ЭДО":
        await update_user_balance(report["user_id"], report['amount'])

    await delete_document(data)
    await delete_last_message(report["user_id"])
