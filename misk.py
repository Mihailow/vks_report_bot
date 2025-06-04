import asyncio
import os
import smtplib
import imaplib
import email
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
import re
import logging

from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler

from config import *
from keyboards import *
from postgres import *


class Status(StatesGroup):
    new_add_document = State()
    new_add_company = State()
    new_add_facility = State()
    new_add_comment = State()

    old_add_comment = State()


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
        admin = await get_admin(user_id)
        if admin is None:
            raise CancelHandler()


middleware = CheckBotStatusMiddleware()
dp.middleware.setup(middleware)


async def change_buttons():
    commands = [BotCommand(command='start', description='Старт')]
    await bot.set_my_commands(commands, BotCommandScopeDefault())


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

    try:
        mes = await bot.send_message(chat_id, text=text, reply_markup=keyboard, reply_to_message_id=reply)
        logging.info(f"\n   Бот ответил пользователю {mes.chat.id}\n"
                     f"   Id сообщения: {mes.message_id}\n"
                     f"   Текст сообщения: {mes.text}\n")
    except Exception as e:
        logging.error(f"send_message {chat_id}", exc_info=True)
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
    if "document_name" in data and data["document_name"] is not None:
        try:
            os.remove(data["document_name"])
        except Exception as e:
            pass


async def user_do_true(doc_id):
    await asyncio.sleep(3600)
    admins = await get_admins()
    document = await get_document(doc_id)
    for user_id in document["confirms"]:
        if not admins[user_id]["necessary"]:
            if document["confirms"][user_id] is None:
                await update_document_confirms(document["document_id"], user_id, True)
                await change_document_message(document["document_id"])


async def create_document_text(document, admins):
    text = ""
    keyboard = await confirm_keyboard(document["document_id"])
    confirm_text = ""
    count = 0
    yes = 0

    for user_id in document["confirms"]:
        confirm_text += admins[user_id]["name"] + ": "
        if document["confirms"][user_id]:
            confirm_text += "✅"
            count += 1
            yes += 1
        elif document["confirms"][user_id] is not None:
            confirm_text += "❌"
            count += 1
        confirm_text += "\n"
    if document["status"]:
        keyboard = None
    elif count == len(document["confirms"]):
        if document["status"] != "🟢 Оплачено 🟢":
            document["status"] = "🔴 Отменено 🔴"
            if yes == count:
                document["status"] = "🔵 Отправлено 🔵"
            await update_document_status(document["document_id"], document["status"])
        keyboard = None

    if document["status"]:
        text += document["status"] + "\n\n"
    text += document["company"] + "\n\n"
    if document["facility"]:
        text += document["facility"] + "\n\n"
    if document["text"]:
        text += document["text"] + "\n\n"
    for comment in document["comments"]:
        text += comment + "\n"
    if document["comments"]:
        text += "\n"
    text += confirm_text
    return document, text, keyboard


async def send_document(doc_id):
    document = await get_document(doc_id)
    admins = await get_admins()
    document, text, keyboard = await create_document_text(document, admins)
    keyboard = await confirm_keyboard(doc_id)
    messages = {}
    file_id = None
    for user_id in document["confirms"]:
        try:
            if document["document_name"]:
                mes = await send_message(user_id, text, keyboard, document['document_name'])
                file_id = mes.document.file_id
            else:
                mes = await send_message(user_id, text, keyboard)
            messages[user_id] = mes.message_id
        except Exception as e:
            logging.error(f"send_document {user_id}", exc_info=True)
    await delete_document(document)
    await update_document_file_id(doc_id, file_id)
    await update_document_message_id(doc_id, messages)


async def change_document_message(doc_id):
    document = await get_document(doc_id)
    admins = await get_admins()
    document, text, keyboard = await create_document_text(document, admins)

    for user_id in document["confirms"]:
        try:
            if document["document_name"]:
                await change_message(user_id, document["message_id"][user_id], text, keyboard, True)
            else:
                await change_message(user_id, document["message_id"][user_id], text, keyboard)
        except Exception as e:
            logging.error(f"change_document_message {user_id}", exc_info=True)
    if document["status"] == "🔵 Отправлено 🔵":
        # try:
        await send_message_email(document)
        # except:
        #     await update_document_status(document["document_id"], "🔴 Ошибка отправки🔴")
        #     await change_document_message(doc_id)


async def send_message_email(document):
    try:
        if document["document_name"]:
            await bot.download_file_by_id(file_id=document["file_id"],
                                          destination=document["document_name"])
    except Exception as e:
        logging.error(f"send_message_email download_file_by_id {document['file_id']} {document['document_name']}",
                      exc_info=True)

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = dest_email
    msg["Date"] = formatdate(localtime=True)
    msg["Subject"] = subject

    text = "doc_num:" + str(document["document_id"]) + "\n"
    if document["facility"]:
        text += "Объект: " + str(document["facility"]) + "\n"
    text += "Автор: " + str(document["creator"]) + "\n"
    for comment in document["comments"]:
        text += comment + "\n"
    text += "\n"

    if document["document_name"]:
        msg.attach(MIMEText(text))
        with open(f"{document['document_name']}", "rb") as fil:
            part = MIMEApplication(
                fil.read(),
                Name=document["document_name"]
            )
        part["Content-Disposition"] = 'attachment; filename="%s"' % document["document_name"]
        msg.attach(part)
    else:
        text += document["text"]
        msg.attach(MIMEText(text))

    server = smtplib.SMTP_SSL("smtp.ya.ru", 465)
    server.login(from_email, from_email_password)
    server.sendmail(from_email, dest_email, msg.as_string())
    server.quit()

    try:
        os.remove(document["document_name"])
    except Exception as e:
        logging.error(f"send_message_email remove {document['document_name']}",
                      exc_info=True)


async def read_messages():
    try:
        connection = imaplib.IMAP4_SSL(host="imap.yandex.ru", port=993)
        connection.login(user=from_email, password=from_email_password)
        status, msgs = connection.select("INBOX")
        assert status == "OK"
    except Exception as e:
        logging.error(f"read_messages", exc_info=True)
        return

    typ, mail_data = connection.search(None, f'HEADER FROM "{dest_email}"')
    for num in mail_data[0].split():
        typ, message_data = connection.fetch(num, "(RFC822)")
        doc_id = re.search("doc_num:(\d+)", str(message_data[0][1])).group(1)
        mail = email.message_from_bytes(message_data[0][1])
        connection.store(num, "+FLAGS", "\\Deleted")
        if mail.is_multipart():
            for part in mail.walk():
                filename = part.get_filename()
                if filename:
                    with open(f"Оплата {doc_id}.pdf", "wb") as new_file:
                        new_file.write(part.get_payload(decode=True))
                    await send_paid_document(int(doc_id))
    connection.expunge()
    connection.close()
    connection.logout()


async def send_paid_document(doc_id):
    document = await get_document(doc_id)
    if document is not None:
        await update_document_status(doc_id, "🟢 Оплачено 🟢")
        await change_document_message(doc_id)
        document = await get_document(doc_id)

        for user_id in document["confirms"]:
            await send_message(user_id, None, None, f"Оплата {doc_id}.pdf", document["message_id"][user_id])
    try:
        os.remove(f"Оплата {doc_id}.pdf")
    except Exception as e:
        logging.error(f"send_paid_document remove Оплата {doc_id}.pdf",
                      exc_info=True)
