from postgres_queries import *


async def get_admin(tg_id):
    admin = await postgres_select_one("SELECT * FROM admins WHERE tg_id = %s AND report_bot IS NOT NULL;",
                                      (tg_id,))
    return admin


async def get_admins():
    admins = await postgres_select_all("SELECT * FROM admins WHERE report_bot IS NOT NULL ORDER BY name;",
                                       None)
    return admins


async def update_user_tg_id(tg_id, secret_key):
    await postgres_do_query("UPDATE report_users SET tg_id = %s, secret_key = NULL WHERE secret_key = %s;",
                            (tg_id, secret_key,))


async def get_user(tg_id):
    user = await postgres_select_one("SELECT * FROM report_users WHERE tg_id = %s AND status = true;",
                                     (tg_id,))
    return user


async def get_user_by_password(secret_key):
    user = await postgres_select_one("SELECT * FROM report_users WHERE secret_key = %s;",
                                     (secret_key,))
    return user


async def get_companies():
    companies = await postgres_select_all("SELECT * FROM companies WHERE status = true ORDER BY name;",
                                          None)
    return companies


async def get_company(company_id):
    company = await postgres_select_one("SELECT * FROM companies WHERE company_id = %s;",
                                        (company_id,))
    return company


async def get_facility(facility_id):
    facility = await postgres_select_one("SELECT * FROM facilities WHERE facility_id = %s;",
                                         (facility_id,))
    return facility


async def get_facilities(company_id):
    facilities = await postgres_select_all("SELECT * FROM facilities WHERE status = true AND "
                                           "company_id = %s ORDER BY name;",
                                           (company_id,))
    return facilities


async def insert_report(data):
    print(data)
    report = await postgres_select_one("INSERT INTO reports (user_id, document_name, facility_id, document_number, "
                                       "amount, date, purpose, type, upd_type) VALUES ((SELECT user_id FROM "
                                       "report_users WHERE tg_id = %s), %s, %s, %s, %s, %s, %s, %s, %s) "
                                       "RETURNING report_id;",
                                       (data["user_id"], data["document_name"], data["facility_id"],
                                        data["document_number"], data["amount"], data["date"],
                                        data["purpose"], data["type"], data["upd_type"]))
    return report


async def update_report_file_id(report_id, file_id):
    await postgres_do_query("UPDATE reports SET file_id = %s WHERE report_id = %s;",
                            (file_id, report_id))


async def update_report_sent(report_id):
    await postgres_do_query("UPDATE reports SET sent = NOW() WHERE report_id = %s;",
                            (report_id,))


async def update_report_received(report_id):
    await postgres_do_query("UPDATE reports SET received = NOW() WHERE report_id = %s;",
                            (report_id,))


async def get_report(report_id):
    report = await postgres_select_one("SELECT reports.report_id, report_users.name AS creator, "
                                       "reports.document_number, companies.name AS company, facilities.name AS "
                                       "facility, reports.amount, reports.date, reports.purpose, reports.type, "
                                       "reports.upd_type, reports.document_name FROM reports, report_users, companies, "
                                       "facilities WHERE reports.user_id = report_users.user_id AND "
                                       "reports.facility_id = facilities.facility_id AND facilities.company_id = "
                                       "companies.company_id AND reports.report_id = %s",
                                       (report_id,))
    return report


async def get_registry_reports_for_user(tg_id):
    reports = await postgres_select_all("SELECT report_id, document_number, date, amount FROM reports WHERE "
                                        "user_id = (SELECT user_id FROM report_users WHERE tg_id = %s) "
                                        "AND type IS DISTINCT FROM 'без чека' AND upd_type IS DISTINCT FROM 'ЭДО' "
                                        "AND sent IS NULL;",
                                        (tg_id,))
    return reports


async def get_users_with_reports():
    users = await postgres_select_all("SELECT DISTINCT report_users.name, report_users.user_id "
                                      "FROM reports, report_users WHERE reports.user_id = report_users.user_id "
                                      "AND report_users.status = true AND reports.sent IS NOT NULL "
                                      "AND reports.received IS NULL;",
                                      None)
    return users


async def get_registry_reports_for_admin(user_id):
    reports = await postgres_select_all("SELECT report_id, document_number, date, amount, sent FROM reports"
                                        " WHERE user_id = %s AND type IS DISTINCT FROM 'без чека' AND upd_type IS "
                                        "DISTINCT FROM 'ЭДО' AND sent IS NOT NULL AND received IS NULL;",
                                        (user_id,))
    return reports
