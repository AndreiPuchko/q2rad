#    Copyright © 2021 Andrei Puchko
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import sys


from q2db.cursor import Q2Cursor
from q2db.db import Q2Db
from q2gui.q2model import Q2CursorModel
from q2gui.q2utils import int_, num
from q2gui import q2app
from q2gui.q2dialogs import q2Mess, Q2WaitShow

# import html
import datetime
import calendar


from q2rad import Q2Form
from q2gui.q2form import NEW, COPY

import urllib.request
from socket import error as SocketError

if "darwin" in sys.platform:
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context

# import errno


def open_url(url, timeout=5):
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
    except SocketError:
        response = None
    return response


def read_url(url, waitbar=False, chunk_size=10000000):
    urlop = open_url(url)
    if urlop:
        if waitbar:
            datalen = int_(urlop.headers["content-length"])
            chunk_count = int(datalen / chunk_size)
            rez = b""
            if chunk_count > 1:
                w = Q2WaitShow(chunk_count)
                while True:
                    chunk = urlop.read(chunk_size)
                    if chunk:
                        rez += chunk
                    else:
                        break
                    w.step()
                w.close()
                return rez
        else:
            return urlop.read()
    else:
        return b""


def get_default_db(q2_db):
    if q2_db is None:
        q2_db = q2app.q2_app.db_data
    return q2_db


def insert(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.insert(table, row)


def insert_if_not_exists(table, row, key_column, q2_db=None):
    q2_db: Q2Db = get_default_db(q2_db)
    value = row.get(key_column, "0")
    if q2_db.get(table, f"{key_column} = '{value}'") == {}:
        if key_column not in row:
            row[key_column] = value
        if "name" not in row:
            row["name"] = "-"
        return q2_db.insert(table, row)
    else:
        return True


insert_if_not_exist = insert_if_not_exists


def raw_insert(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.raw_insert(table, row)


def update(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.update(table, row)


def upsert(table, where, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.upsert(table, where, row)


def last_error(q2_db=None):
    return get_default_db(q2_db).last_sql_error


def get(table="", where="", column="", q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.get(table, where, column)


def delete(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.delete(table, row)


def transaction(q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.transaction()


def commit(q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.commit()


def rollback(q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.rollback()


def today():
    return str(datetime.date.today())


def ensure_empty_pk(table="", row={}, q2_db=None):
    q2_db = get_default_db(q2_db)
    q2_db.ensure_empty_pk(table, row)


def ensure_record(table_name="", where="", record={}, q2_db=None):
    q2_db = get_default_db(q2_db)
    q2_db.ensure_record(table_name, where, record)


def dtoc(date, format_from="%Y-%m-%d", format_to="%d.%m.%Y"):
    try:
        return datetime.datetime.strptime(date, format_from).strftime(format_to)
    except Exception:
        return ""


def ctod(date, format_from="%d.%m.%Y", format_to="%Y-%m-%d"):
    try:
        return dtoc(date, format_from, format_to)
    except Exception:
        return ""


def first_day_of_month(date):
    try:
        _date = datetime.datetime.strptime(date, "%Y-%m-%d")
        _date = _date.replace(day=1)
        return _date.strftime("%Y-%m-%d")
    except Exception:
        return date


def last_day_of_month(date):
    try:
        _date = datetime.datetime.strptime(date, "%Y-%m-%d")
        _date = _date.replace(day=calendar.monthrange(_date.year, _date.month)[1])
        return _date.strftime("%Y-%m-%d")
    except Exception:
        return date


def ffinder(module_name="module", function_name="fname"):
    from q2rad.q2rad import run_module

    glo = {}
    glo.update(globals())
    run_module(module_name, import_only=True, _globals=glo)
    if function_name in glo:
        return glo[function_name]
    else:

        def empty_function(*args, **kwargs):
            pass

        return empty_function
