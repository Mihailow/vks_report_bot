import datetime
from calendar import Calendar
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup


month_names = {1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель", 5: "Май", 6: "Июнь",
               7: "Июль", 8: "Август", 9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь"}


async def make_calendar(month=None, year=None):
    today = datetime.date.today()
    calendar = Calendar()
    if month is None:
        month = today.month
    if year is None:
        year = today.year
    dates = calendar.monthdatescalendar(year, month)
    return dates, month, year, today


async def user_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Добавить документ"))
    keyboard.add(KeyboardButton(text="Сформировать реестр"))
    return keyboard


async def admin_main_keyboard():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton(text="Сформировать реестр"))
    return keyboard


async def add_document_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Нет документа", callback_data="no_document"))
    keyboard.add(InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def company_keyboard(companies):
    keyboard = InlineKeyboardMarkup()
    for company in companies:
        keyboard.add(InlineKeyboardButton(text=company["name"], callback_data=f"set_company_{company['company_id']}"))
    keyboard.row(InlineKeyboardButton(text="↩️", callback_data="back"),
                 InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def facility_keyboard(facilities):
    keyboard = InlineKeyboardMarkup()
    for facility in facilities:
        keyboard.add(InlineKeyboardButton(text=facility["name"], callback_data=f"set_facility_{facility['facility_id']}"))
    keyboard.row(InlineKeyboardButton(text="↩️", callback_data="back"),
                 InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def type_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="УПД", callback_data="type_upd"))
    keyboard.add(InlineKeyboardButton(text="ЧЕК", callback_data="type_check"))
    keyboard.row(InlineKeyboardButton(text="↩️", callback_data="back"),
                 InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def upd_type_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="ЭДО", callback_data="upd_type_edo"))
    keyboard.add(InlineKeyboardButton(text="БУМАГА", callback_data="upd_type_bumaga"))
    keyboard.row(InlineKeyboardButton(text="↩️", callback_data="back"),
                 InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def document_registry_keyboard(marked, doc_id):
    keyboard = InlineKeyboardMarkup()
    if marked:
        keyboard.add(InlineKeyboardButton(text="✅", callback_data=f"document_registry_accept_{doc_id}"))
    else:
        keyboard.add(InlineKeyboardButton(text="☑", callback_data=f"document_registry_accept_{doc_id}"))
    return keyboard


async def document_registry_users_with_reports_keyboard(users):
    keyboard = InlineKeyboardMarkup()
    for user in users:
        keyboard.add(InlineKeyboardButton(text=str(user["name"]),
                                          callback_data=f"show_document_registry_user_{user['user_id']}"))
    keyboard.add(InlineKeyboardButton(text="🚫 Отмена 🚫", callback_data="cancel"))
    return keyboard


async def document_registry_receive_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Принять документы", callback_data="receive_document_registry"))
    keyboard.add(InlineKeyboardButton(text="🚫 Отмена 🚫", callback_data="cancel"))
    return keyboard


async def back_cancel_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(text="↩️", callback_data="back"),
                 InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def calendar_keyboard(month=None, year=None):
    calendar, month, year, today = await make_calendar(month, year)
    keyboard = InlineKeyboardMarkup()
    keyboard.row(InlineKeyboardButton(text="◀️",
                                      callback_data=f"year_back_{month}_{year}"),
                 InlineKeyboardButton(text=year,
                                      callback_data="nothing"),
                 InlineKeyboardButton(text="▶️",
                                      callback_data=f"year_forward_{month}_{year}"))
    keyboard.row(InlineKeyboardButton(text="◀️",
                                      callback_data=f"month_back_{month}_{year}"),
                 InlineKeyboardButton(text=month_names[month],
                                      callback_data="nothing"),
                 InlineKeyboardButton(text="▶️",
                                      callback_data=f"month_forward_{month}_{year}"))
    for week in calendar:
        button_list = []
        for day in week:
            if day.month != month:
                button_list.append(InlineKeyboardButton(text=" ",
                                                        callback_data=f"nothing"))
            elif day == today:
                button_list.append(InlineKeyboardButton(text=f"🟢{day.day}",
                                                        callback_data=f"date_{day}"))
            else:
                button_list.append(InlineKeyboardButton(text=str(day.day),
                                                        callback_data=f"date_{day}"))
        keyboard.row(*button_list)
    keyboard.row(InlineKeyboardButton(text="↩️", callback_data="back"),
                 InlineKeyboardButton(text="🚫", callback_data="cancel"))
    return keyboard


async def document_registry_send_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(text="Отправить документы", callback_data="send_document_registry"))
    keyboard.add(InlineKeyboardButton(text="🚫 Отмена 🚫", callback_data="cancel"))
    return keyboard
