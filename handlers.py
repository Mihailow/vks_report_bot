from misk import *


@dp.message_handler(commands=["start"], state="*")
async def command_start(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_last_messages(message.from_user.id)
    await delete_document(await state.get_data())

    admin = await get_admin(message.from_user.id)
    if admin is not None:
        keyboard = await admin_main_keyboard()
    else:
        keyboard = await user_main_keyboard()
    text = "Здравствуйте!"
    await send_message(message.from_user.id, text, keyboard)

    await state.finish()


@dp.message_handler(text="Добавить документ", state="*")
async def add_document(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_last_messages(message.from_user.id)
    await delete_document(await state.get_data())

    text = "⬇️ Отправьте фотографию или документ ⬇️"
    keyboard = await add_document_keyboard()
    await send_last_message(message.from_user.id, text, keyboard)

    await state.finish()
    await state.update_data(user_id=message.from_user.id)
    await state.update_data(upd_type=None)
    await state.set_state(Status.user_add_document)


@dp.message_handler(text="Сформировать реестр", state="*")
async def add_document(message: types.Message, state: FSMContext):
    await delete_last_message(message.from_user.id)
    await delete_last_messages(message.from_user.id)
    await delete_document(await state.get_data())

    admin = await get_admin(message.from_user.id)
    if admin is None:
        reports = await get_registry_reports_for_user(message.from_user.id)

        if not reports:
            text = "У вас отсутствуют документы"
            await send_last_messages(message.from_user.id, text)
        else:
            text = "--------------------------------------------"
            await send_last_messages(message.from_user.id, text)

            for report in reports:
                report["accept"] = False

                text = (f"Номер: {report['document_number']}\n"
                        f"Дата: {report['date']}\n"
                        f"Сумма: {report['amount']}\n")
                keyboard = await document_registry_keyboard(report["accept"], report["report_id"])
                mes = await send_last_messages(message.from_user.id, text, keyboard)
                report["mes_id"] = mes.message_id

            text = "--------------------------------------------"
            keyboard = await document_registry_send_keyboard()
            await send_last_messages(message.from_user.id, text, keyboard)

            await state.finish()
            await state.update_data(reports=reports)
            await state.set_state(Status.user_document_registry)
    else:
        users = await get_users_with_reports()
        if not users:
            text = "Отсутствуют новые документы"
            await send_last_message(message.from_user.id, text)
            await state.finish()
        else:
            text = "⬇️ Выберите ФИО из списка ⬇️"
            keyboard = await document_registry_users_with_reports_keyboard(users)
            await send_last_message(message.from_user.id, text, keyboard)

            await state.finish()
            await state.set_state(Status.admin_document_registry)


@dp.message_handler(state=Status.user_add_document, content_types=types.ContentType.ANY)
async def status_new_add_document(message: types.Message, state: FSMContext):
    if message.content_type == "photo":
        document_name = f"{datetime.datetime.now().strftime('%d-%m-%Y %H.%M.%S')}.png"
        await message.photo[-1].download(destination_file=document_name)
        await state.update_data(document_name=document_name)
    elif message.content_type == "document":
        document_name = message.document.file_name
        await message.document.download(destination_file=document_name)
        await state.update_data(document_name=document_name)
    else:
        text = "Я вас не понял\n⬇️ Отправьте фотографию или документ ⬇️"
        keyboard = await add_document_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return
    companies = await get_companies()

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await company_keyboard(companies)
    await send_last_message(message.from_user.id, text, keyboard)
    await state.set_state(Status.user_add_company)


@dp.callback_query_handler(text="no_document", state=Status.user_add_document)
async def but_no_document(callback_query: types.CallbackQuery, state: FSMContext):
    companies = await get_companies()

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await company_keyboard(companies)
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.update_data(document_name=None)
    await state.update_data(type="без чека")
    await state.set_state(Status.user_add_company)


@dp.callback_query_handler(text_startswith="set_company_", state=Status.user_add_company)
async def but_set_company_(callback_query: types.CallbackQuery, state: FSMContext):
    company_id = callback_query.data.replace("set_company_", "")
    facilities = await get_facilities(company_id)

    text = "⬇️ Выберите пункт меню ⬇️"
    keyboard = await facility_keyboard(facilities)
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.user_add_facility)
    await state.update_data(company_id=company_id)


@dp.callback_query_handler(text_startswith="set_facility_", state=Status.user_add_facility)
async def bet_set_facility_(callback_query: types.CallbackQuery, state: FSMContext):
    facility_id = callback_query.data.replace("set_facility_", "")

    text = "Введите номер документа"
    keyboard = await back_cancel_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.set_state(Status.user_add_document_number)
    await state.update_data(facility_id=facility_id)


@dp.message_handler(state=Status.user_add_document_number, content_types=types.ContentType.ANY)
async def status_payment_amount(message: types.Message, state: FSMContext):
    if message.content_type != "text":
        text = "Не могу прочитать значение\nВведите номер документа текстом"
        keyboard = await back_cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return

    await state.update_data(document_number=message.text)

    text = "Введите сумму"
    keyboard = await back_cancel_keyboard()
    await send_last_message(message.from_user.id, text, keyboard)

    await state.set_state(Status.user_add_amount)


@dp.message_handler(state=Status.user_add_amount, content_types=types.ContentType.ANY)
async def status_payment_amount(message: types.Message, state: FSMContext):
    if message.content_type != "text":
        text = "Не могу прочитать значение\nВведите сумму цифрами\nКопейки через точку"
        keyboard = await back_cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return
    message.text = message.text.replace(",", ".")
    try:
        float(message.text)
    except Exception as e:
        logging.error(f"status_payment_amount {message.from_user.id} {message.text}", exc_info=True)
        text = "Не могу прочитать значение\nВведите сумму цифрами\nКопейки через точку"
        keyboard = await back_cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return

    text = "Выберите дату"
    keyboard = await calendar_keyboard()
    await send_last_message(message.from_user.id, text, keyboard)

    await state.update_data(amount=message.text)
    await state.set_state(Status.user_add_date)


@dp.callback_query_handler(text_startswith="date_", state=Status.user_add_date)
async def but_payment_date_payment_date_(callback_query: types.CallbackQuery, state: FSMContext):
    date = callback_query.data.replace("date_", "")

    text = "Введите назначение"
    keyboard = await back_cancel_keyboard()
    await send_last_message(callback_query.from_user.id, text, keyboard)

    await state.update_data(date=date)
    await state.set_state(Status.user_add_purpose)


@dp.message_handler(state=Status.user_add_purpose, content_types=types.ContentType.ANY)
async def status_payment_amount(message: types.Message, state: FSMContext):
    if message.content_type != "text":
        text = "Не могу прочитать значение\nВведите назначение текстом"
        keyboard = await back_cancel_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)
        return

    await state.update_data(purpose=message.text)

    if "type" in await state.get_data():
        await add_report(await state.get_data())
    else:
        text = "⬇️ Выберите пункт меню ⬇️"
        keyboard = await type_keyboard()
        await send_last_message(message.from_user.id, text, keyboard)

        await state.set_state(Status.user_add_type)


@dp.callback_query_handler(text_startswith="type_", state=Status.user_add_type)
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    report_type = callback_query.data.replace("type_", "")
    if report_type == "upd":
        report_type = "УПД"

        text = "⬇️ Выберите пункт меню ⬇️"
        keyboard = await upd_type_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        await state.update_data(type=report_type)
        await state.set_state(Status.user_add_upd_type)
    elif report_type == "check":
        report_type = "чек"

        await state.update_data(type=report_type)
        await add_report(await state.get_data())


@dp.callback_query_handler(text_startswith="upd_type_", state=Status.user_add_upd_type)
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    report_type = callback_query.data.replace("upd_type_", "")
    if report_type == "edo":
        report_type = "ЭДО"
    elif report_type == "bumaga":
        report_type = "бумага"

    await state.update_data(upd_type=report_type)
    await add_report(await state.get_data())


@dp.callback_query_handler(text_startswith="document_registry_accept_", state=Status.user_document_registry)
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    report_id = callback_query.data.replace("document_registry_accept_", "")
    reports = (await state.get_data())["reports"]
    for report in reports:
        if report["report_id"] == int(report_id):
            report["accept"] = not report["accept"]
            text = (f"Номер: {report['document_number']}\n"
                    f"Дата: {report['date']}\n"
                    f"Сумма: {report['amount']}\n")
            keyboard = await document_registry_keyboard(report["accept"], report["report_id"])
            await change_message(callback_query.from_user.id, report["mes_id"], text, keyboard)
            break

    await state.update_data(reports=reports)


@dp.callback_query_handler(text="send_document_registry", state=Status.user_document_registry)
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    reports = (await state.get_data())["reports"]
    for report in reports:
        if report["accept"]:
            await update_report_sent(report["report_id"])

    await delete_last_messages(callback_query.from_user.id)
    await state.finish()

    text = "Документы отправлены"
    await send_message(callback_query.from_user.id, text)


@dp.callback_query_handler(text_startswith="show_document_registry_user_", state=Status.admin_document_registry)
async def but_set_company_(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.data.replace("show_document_registry_user_", "")
    reports = await get_registry_reports_for_admin(user_id)

    await delete_last_messages(callback_query.from_user.id)

    text = "--------------------------------------------"
    await send_last_messages(callback_query.from_user.id, text)

    for report in reports:
        report["accept"] = False

        text = (f"Номер: {report['document_number']}\n"
                f"Дата: {report['date']}\n"
                f"Сумма: {report['amount']}\n"
                f"Отправлено: {report['sent']}\n")
        keyboard = await document_registry_keyboard(report["accept"], report["report_id"])
        mes = await send_last_messages(callback_query.from_user.id, text, keyboard)
        report["mes_id"] = mes.message_id

    text = "--------------------------------------------"
    keyboard = await document_registry_receive_keyboard()
    await send_last_messages(callback_query.from_user.id, text, keyboard)

    await state.update_data(reports=reports)


@dp.callback_query_handler(text_startswith="document_registry_accept_", state=Status.admin_document_registry)
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    report_id = callback_query.data.replace("document_registry_accept_", "")
    reports = (await state.get_data())["reports"]
    for report in reports:
        if report["report_id"] == int(report_id):
            report["accept"] = not report["accept"]
            text = (f"Номер: {report['document_number']}\n"
                    f"Дата: {report['date']}\n"
                    f"Сумма: {report['amount']}\n"
                    f"Отправлено: {report['sent']}\n")
            keyboard = await document_registry_keyboard(report["accept"], report["report_id"])
            await change_message(callback_query.from_user.id, report["mes_id"], text, keyboard)
            break

    await state.update_data(reports=reports)


@dp.callback_query_handler(text="receive_document_registry", state=Status.admin_document_registry)
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    reports = (await state.get_data())["reports"]
    for report in reports:
        if report["accept"]:
            await update_report_received(report["report_id"])
            await update_user_balance(report["user_id"], report["amount"])

    await delete_last_messages(callback_query.from_user.id)
    await delete_last_message(callback_query.from_user.id)

    users = await get_users_with_reports()
    if not users:
        await state.finish()
    else:
        text = "⬇️ Выберите ФИО из списка ⬇️"
        keyboard = await document_registry_users_with_reports_keyboard(users)
        await send_last_message(callback_query.from_user.id, text, keyboard)

        await state.finish()
        await state.set_state(Status.admin_document_registry)

    text = "Документы приняты"
    await send_message(callback_query.from_user.id, text)


@dp.callback_query_handler(text="back", state="*")
async def but_back(callback_query: types.CallbackQuery, state: FSMContext):
    current_state = await state.get_state()
    current_data = await state.get_data()

    if current_state == "Status:user_add_company":
        text = "⬇️ Отправьте фотографию или документ ⬇️"
        keyboard = await add_document_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        await state.finish()
        await state.update_data(user_id=callback_query.from_user.id)
        await state.update_data(upd_type=None)
        await state.set_state(Status.user_add_document)
    elif current_state == "Status:user_add_facility":
        companies = await get_companies()

        text = "⬇️ Выберите пункт меню ⬇️"
        keyboard = await company_keyboard(companies)
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("company_id")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_company)
    elif current_state == "Status:user_add_document_number":
        company_id = current_data["company_id"]
        facilities = await get_facilities(company_id)

        text = "⬇️ Выберите пункт меню ⬇️"
        keyboard = await facility_keyboard(facilities)
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("facility_id")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_facility)
    elif current_state == "Status:user_add_amount":
        text = "Введите номер документа"
        keyboard = await back_cancel_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("document_number")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_document_number)
    elif current_state == "Status:user_add_date":
        text = "Введите сумму"
        keyboard = await back_cancel_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("amount")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_amount)
    elif current_state == "Status:user_add_purpose":
        text = "Выберите дату"
        keyboard = await calendar_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("date")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_date)
    elif current_state == "Status:user_add_type":
        text = "Введите назначение"
        keyboard = await back_cancel_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("purpose")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_purpose)
    elif current_state == "Status:user_add_upd_type":
        text = "⬇️ Выберите пункт меню ⬇️"
        keyboard = await type_keyboard()
        await send_last_message(callback_query.from_user.id, text, keyboard)

        current_data.pop("type")
        await state.set_data(current_data)
        await state.set_state(Status.user_add_type)


@dp.callback_query_handler(text="cancel", state="*")
async def but_cancel(callback_query: types.CallbackQuery, state: FSMContext):
    await delete_last_message(callback_query.from_user.id)
    await delete_last_messages(callback_query.from_user.id)
    await delete_document(await state.get_data())
    await state.finish()


@dp.callback_query_handler(text_startswith="year_back_", state="*")
async def but_payment_year_back_(callback_query: types.CallbackQuery, state: FSMContext):
    month, year = callback_query.data.replace("year_back_", "").split("_")
    year = int(year) - 1

    text = "Выберите дату"
    keyboard = await calendar_keyboard(int(month), int(year))
    await change_message(callback_query.from_user.id, callback_query.message.message_id, text, keyboard)


@dp.callback_query_handler(text_startswith="year_forward_", state="*")
async def payment_year_forward_(callback_query: types.CallbackQuery, state: FSMContext):
    month, year = callback_query.data.replace("year_forward_", "").split("_")
    year = int(year) + 1

    text = "Выберите дату"
    keyboard = await calendar_keyboard(int(month), int(year))
    await change_message(callback_query.from_user.id, callback_query.message.message_id, text, keyboard)


@dp.callback_query_handler(text_startswith="month_back_", state="*")
async def but_payment_month_back_(callback_query: types.CallbackQuery, state: FSMContext):
    month, year = callback_query.data.replace("month_back_", "").split("_")
    month = int(month) - 1
    if month == 0:
        month = 12
        year = int(year) - 1

    text = "Выберите дату"
    keyboard = await calendar_keyboard(int(month), int(year))
    await change_message(callback_query.from_user.id, callback_query.message.message_id, text, keyboard)


@dp.callback_query_handler(text_startswith="month_forward_", state="*")
async def but_payment_month_forward_(callback_query: types.CallbackQuery, state: FSMContext):
    month, year = callback_query.data.replace("month_forward_", "").split("_")
    month = int(month) + 1
    if month == 13:
        month = 1
        year = int(year) + 1

    text = "Выберите дату"
    keyboard = await calendar_keyboard(int(month), int(year))
    await change_message(callback_query.from_user.id, callback_query.message.message_id, text, keyboard)
