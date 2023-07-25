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

if __name__ == "__main__":
    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2db.db import Q2Db
from q2gui.q2model import Q2CursorModel
from q2gui.q2utils import int_, num
from q2gui import q2app
from q2gui.q2dialogs import q2Mess, Q2WaitShow
import html

from q2rad import Q2Form
from q2gui.q2form import NEW, COPY

import urllib.request
from socket import error as SocketError

if "darwin" in sys.platform:
    import ssl

    ssl._create_default_https_context = ssl._create_unverified_context
import datetime

# import errno


def open_url(url):
    try:
        response = urllib.request.urlopen(url)
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


class q2cursor(Q2Cursor):
    def __init__(self, sql="", q2_db=None):
        if q2_db is None:
            q2_db = q2app.q2_app.db_data
        super().__init__(q2_db, sql)
        if q2_db.last_sql_error:
            print(q2_db.last_sql_error)

    def q2form(self):
        form = Q2Form(self.sql)
        for x in self.record(0):
            form.add_control(x, x, datalen=250)
        form.set_model(Q2CursorModel(self))
        return form

    def browse(self):
        if self.row_count() <= 0:
            q2Mess(
                f"""Query<br>
                        <b>{html.escape(self.sql)}</b><br>
                        returned no records,<br>
                        <font color=red>
                        {self.last_sql_error()}
                    """
            )
        else:
            self.q2form().run()
        return self


def get_default_db(q2_db):
    if q2_db is None:
        q2_db = q2app.q2_app.db_data
    return q2_db


def insert(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.insert(table, row)


def insert_if_not_exist(table, row, key_column, q2_db=None):
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


def raw_insert(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.raw_insert(table, row)


def update(table, row, q2_db=None):
    q2_db = get_default_db(q2_db)
    return q2_db.update(table, row)


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
    return datetime.date.today()
