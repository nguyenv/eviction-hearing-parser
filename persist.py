import os
from dotenv import load_dotenv
from connect_to_database import get_database_connection

load_dotenv()
local_dev = os.getenv("LOCAL_DEV") == "true"

def get_case(case_id: str):
    conn = get_database_connection(local_dev=local_dev)

    # conn.row_factory = sqlite3.Row
    curs = conn.cursor()
    curs.execute("SELECT * FROM V_CASE WHERE CASE_NUMBER = ?", (case_id,))
    case = curs.fetchone()
    curs.close()
    return dict(case)


def rest_case(case):
    """
    Takes a dictionary representation of a case and maps it in to a PostgreSQL DB
    """
    conn = get_database_connection(local_dev=local_dev)
    # conn.execute("pragma journal_mode=wal")

    curs = conn.cursor()
    curs.execute(
    """
    INSERT INTO CASE_DETAIL
    (CASE_NUMBER, STATUS, REGISTER_URL, PRECINCT, STYLE, PLAINTIFF, DEFENDANTS, PLAINTIFF_ZIP, DEFENDANT_ZIP, CASE_TYPE)
    VALUES (%(case_num)s, %(status)s, %(reg_url)s, %(prec_num)s, %(style)s, %(plaint)s, %(defend)s, %(plaint_zip)s, %(defend_zip)s, %(type)s)
    ON CONFLICT(CASE_NUMBER)
    DO UPDATE SET
    (STATUS, REGISTER_URL, PRECINCT, STYLE, PLAINTIFF, DEFENDANTS, PLAINTIFF_ZIP, DEFENDANT_ZIP, CASE_TYPE) =
    (%(status)s, %(reg_url)s, %(prec_num)s, %(style)s, %(plaint)s, %(defend)s, %(plaint_zip)s, %(defend_zip)s, %(type)s)
    """,
        {
            'case_num': case["case_number"],
            'status': case["status"],
            'reg_url': case["register_url"],
            'prec_num': case["precinct_number"],
            'style': case["style"],
            'plaint': case["plaintiff"],
            'defend': case["defendants"],
            'plaint_zip': case["plaintiff_zip"],
            'defend_zip': case["defendant_zip"],
            'type': case["type"]
        },
    )

    curs.execute(
    """
    INSERT INTO DISPOSITION
    (CASE_NUMBER, TYPE, DATE, AMOUNT, AWARDED_TO, AWARDED_AGAINST)
    VALUES (%(case_num)s, %(disp_type)s, %(disp_date)s, %(disp_amt)s, %(disp_to)s, %(disp_against)s)
    ON CONFLICT(CASE_NUMBER)
    DO UPDATE SET
    (TYPE, DATE, AMOUNT, AWARDED_TO, AWARDED_AGAINST) =
    (%(disp_type)s, %(disp_date)s, %(disp_amt)s, %(disp_to)s, %(disp_against)s)
    """,
        {
            'case_num': case["case_number"],
            'disp_type': case["disposition_type"],
            'disp_date': case["disposition_date"],
            'disp_amt': str(case["disposition_amount"]),
            'disp_to': case["disposition_awarded_to"],
            'disp_against': case["disposition_awarded_against"],
        },
    )
    # TODO scrape all event types in a similar way (writs should be consolidated in)
    # Types should mirror the values from the HTML table headers, HR/ER/SE/etc.
    for hearing_number, hearing in enumerate(case["hearings"]):
        curs.execute(
            """
            INSERT INTO EVENT
            (CASE_NUMBER, EVENT_NUMBER, DATE, TIME, OFFICER, RESULT, TYPE)
            VALUES (%(case_num)s, %(hearing_num)s, %(hearing_date)s, %(hearing_time)s, %(hearing_officer)s, %(hearing_appeared)s, 'HR')
            ON CONFLICT(CASE_NUMBER, EVENT_NUMBER)
            DO UPDATE SET
            (EVENT_NUMBER, DATE, TIME, OFFICER, RESULT, TYPE) =
            (%(hearing_num)s, %(hearing_date)s, %(hearing_time)s, %(hearing_officer)s, %(hearing_appeared)s, 'HR')
            """,
            {
                'case_num': case["case_number"],
                'hearing_num': hearing_number,
                'hearing_date': hearing["hearing_date"],
                'hearing_time': hearing["hearing_time"],
                'hearing_officer': hearing["hearing_officer"],
                'hearing_appeared': hearing["appeared"],
            },
        )
    conn.commit()
    curs.close()
    conn.close()

def rest_setting(setting):
    """
    Takes a dictionary representation of a setting and maps it in to a sqlite DB
    """
    conn = get_database_connection(local_dev=local_dev)
    curs = conn.cursor()
    curs.execute(
    """
    INSERT INTO SETTING
    (CASE_NUMBER, CASE_LINK, SETTING_TYPE, SETTING_STYLE, JUDICIAL_OFFICER, SETTING_DATE, SETTING_TIME, HEARING_TYPE)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT(CASE_NUMBER, SETTING_TYPE, HEARING_TYPE, SETTING_DATE)
    DO NOTHING
    """,
        (
            setting["case_number"],
            setting["case_link"],
            setting["setting_type"],
            setting["setting_style"],
            setting["judicial_officer"],
            setting["setting_date"],
            setting["setting_time"],
            setting["hearing_type"],
        ),
    )
    conn.commit()
    curs.close()
    conn.close()

def get_old_active_case_nums():
    """
    Retrurns list of case nums in CASE_DETAIL table that are still active.
    """
    conn = get_database_connection(local_dev=local_dev)
    curs = conn.cursor()

    curs.execute("""SELECT CASE_NUMBER FROM CASE_DETAIL WHERE LOWER(STATUS) NOT IN
                ('final disposition', 'transferred', 'bankruptcy', 'judgment released',
                'judgment satisfied', 'appealed', 'final status', 'dismissed')""")
    active_case_nums = [tup[0] for tup in curs.fetchall()]
    curs.close()
    conn.close()

    return active_case_nums

# not currently being used for anything
def drop_rows_from_table(table_name: str, case_ids: list):
    """
    Drops all rows with case number in case_ids from table table_name - works for CASE_DETAIL, DISPOSITION, and EVENT tables
    """
    if len(case_ids) == 1:
        case_ids = str(tuple(case_ids)).replace(",", "")
    else:
        case_ids = str(tuple(case_ids))

    conn = get_database_connection(local_dev=local_dev)
    curs = conn.cursor()

    if table_name == "CASE_DETAIL":
        curs.execute("DELETE FROM %s WHERE CASE_NUMBER IN %s", (table_name, case_ids))
    else:
        curs.execute("DELETE FROM %s WHERE CASE_NUMBER IN %s", (table_name, case_ids))

    conn.commit()
    curs.close()
    conn.close()
