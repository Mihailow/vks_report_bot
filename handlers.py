from datetime import datetime

from misk import *


@dp.message_handler(commands=["start"], state="*")
async def command_start(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_document(await state.get_data())

    text = "Здравствуйте!"
    keyboard = await main_keyboard()
    await send_message(message.from_user.id, text, keyboard)

    await state.finish()


@dp.message_handler(text="Добавить документ", state="*")
async def add_document(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_document(await state.get_data())

    confirms = {}
    admins = await get_admins()
    for admin in admins:
        if admin == message.from_user.id:
            confirms[admin] = True
        else:
            confirms[admin] = None

    text = "⬇️ Отправьте текст/картинку/документ(pdf) ⬇️"
    keyboard = await cancel_keyboard()
    await send_last_message(message.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_document)
    await state.update_data(user_id=message.from_user.id)
    await state.update_data(confirms=confirms)
    await state.update_data(status=None)


@dp.message_handler(state=Status.new_add_document, content_types=types.ContentType.ANY)
async def status_new_add_document(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        document_name = f"{datetime.now().strftime('%d-%m-%Y %H.%M.%S')}.png"
        await message.photo[-1].download(destination_file=document_name)
        await state.update_data(text=None)
        await state.update_data(document_name=document_name)
    elif message.content_type == "text":
        await state.update_data(text=message.text)
        await state.update_data(document_name=None)
    elif message.content_type == "document":
        if not message.document.file_name.lower().endswith(".pdf"):
            text = "Документ должен быть pdf!\n⬇️ Отправьте текст/картинку/документ ⬇️"
            keyboard = await cancel_keyboard()
            await send_last_message(message.from_user.id, text, keyboard)
            return
        document_name = message.document.file_name
        await message.document.download(destination_file=document_name)
        await state.update_data(text=None)
        await state.update_data(document_name=document_name)
    else:
        text = "Я вас не понял\n⬇️ Отправьте текст/картинку/документ(pdf) ⬇️"
        keyboard = await cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return
    companies = await get_companies()

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await company_keyboard(companies)
    await send_last_message(message.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_company)


@dp.callback_query_handler(text_startswith="set_company_", state=Status.new_add_company)
async def but_set_company_(callback_query: types.CallbackQuery, state: FSMContext):
    company_id = callback_query.data.replace("set_company_", "")
    company = await get_company(company_id)
    facilities = await get_facilities(company_id)

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await facility_keyboard(facilities)
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_facility)
    await state.update_data(company_id=company_id)
    await state.update_data(company=company["name"])


@dp.message_handler(state=Status.new_add_company, content_types=types.ContentType.ANY)
async def status_new_add_company(message: types.Message, state: FSMContext):
    companies = await get_companies()

    text = "Я вас не понимаю\n⬇️ Выберите пункт меню ⬇️"
    keyboard = await company_keyboard(companies)
    await send_last_message(message.from_user.id, text, keyboard)


@dp.callback_query_handler(text_startswith="set_facility_", state=Status.new_add_facility)
async def bet_set_object_(callback_query: types.CallbackQuery, state: FSMContext):
    facility_name = callback_query.data.replace("set_facility_", "")

    text = "Напишите комментарий\n⬇️ Или выберите пункт меню ⬇️"
    keyboard = await send_without_text_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.new_add_comment)
    if facility_name != "no_facility":
        await state.update_data(facility=facility_name)
    else:
        await state.update_data(facility=None)


@dp.message_handler(state=Status.new_add_facility, content_types=types.ContentType.ANY)
async def status_new_add_object(message: types.Message, state: FSMContext):
    company_id = (await state.get_data())["company_id"]
    facilities = await get_facilities(company_id)

    text = "Я вас не понимаю\n⬇️ Выберите пункт меню ⬇️"
    keyboard = await facility_keyboard(facilities)
    await send_last_message(message.from_user.id, text, keyboard)


@dp.callback_query_handler(text="send_without_text", state=Status.new_add_comment)
async def but_send_without_text(callback_query: types.CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query.from_user.id)
    data = await state.get_data()
    data["comments"] = []

    await state.finish()
    doc_id = await insert_document(data)
    await send_document(doc_id)
    await user_do_true(doc_id)


@dp.message_handler(state=Status.new_add_comment, content_types=types.ContentType.ANY)
async def status_new_add_comment(message: types.Message, state: FSMContext):
    if message.content_type != "text":
        text = "Я вас не понимаю\nНапишите комментарий\n⬇️ Или выберите пункт меню ⬇️"
        keyboard = await send_without_text_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return
    await delete_last_message(message.from_user.id)
    data = await state.get_data()
    admins = await get_admins()
    admin_name = admins[message.from_user.id]["name"]
    data["comments"] = [f"{admin_name}: {message.text}"]

    await state.finish()
    doc_id = await insert_document(data)
    await send_document(doc_id)
    await user_do_true(doc_id)


@dp.callback_query_handler(text="cancel", state="*")
async def but_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query.from_user.id)
    await delete_document(await state.get_data())
    await state.finish()


@dp.callback_query_handler(text_startswith="yes_", state="*")
async def but_yes_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("yes_", "")
    await update_document_confirms(doc_id, callback_query.from_user.id, True)

    await change_document_message(doc_id)


@dp.callback_query_handler(text_startswith="no_", state="*")
async def but_no_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("no_", "")
    await update_document_confirms(doc_id, callback_query.from_user.id, False)

    await change_document_message(doc_id)


@dp.callback_query_handler(text_startswith="add_comment_")
async def but_add_comment_(callback_query: types.CallbackQuery, state: FSMContext):
    doc_id = callback_query.data.replace("add_comment_", "")

    text = "Введите комментарий"
    keyboard = await cancel_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.old_add_comment)
    await state.update_data(doc_id=doc_id)


@dp.message_handler(state=Status.old_add_comment, content_types=types.ContentType.ANY)
async def status_old_add_comment(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    if message.content_type != "text":
        text = "Я вас не понимаю\nВведите комментарий"
        keyboard = await cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return
    doc_id = (await state.get_data())["doc_id"]
    admins = await get_admins()
    admin_name = admins[message.from_user.id]["name"]
    await update_document_comments(doc_id, admin_name, message.text)
    await change_document_message(doc_id)

    await state.finish()


@dp.callback_query_handler(state="*")
async def all_callback(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
