if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2db.db import Q2Db
from q2gui.q2model import Q2CursorModel
from q2gui.q2utils import int_, num
from q2gui import q2app
from q2gui.q2dialogs import q2Mess, q2WaitShow

from q2rad import Q2Form
from q2gui.q2form import NEW, COPY

import urllib.request
from socket import error as SocketError

# import errno


def open_url(url):
    try:
        response = urllib.request.urlopen(url)
    except SocketError as e:
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
                w = q2WaitShow(chunk_count)
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
        return None


class q2cursor(Q2Cursor):
    def __init__(self, sql="", q2_db=None):
        if q2_db is None:
            q2_db = q2app.q2_app.db_data
        super().__init__(q2_db, sql)

    def browse(self):
        if self.row_count() <= 0:
            q2Mess(
                f"""Query<br>
                        <b>{self.sql}</b><br>
                        returned no records,<br>
                        <font color=red>
                        {self.last_sql_error()}
                    """
            )
        else:
            form = Q2Form(self.sql)
            for x in self.record(0):
                form.add_control(x, x, datalen=250)
            form.set_model(Q2CursorModel(self))
            form.run()
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


class SeqMover:
    """create actions for swapping rows in forms, lines, actions"""

    def add_seq_actions(self):
        self.add_action("-")
        self.add_action("Move up", self.move_seq_up, icon="arrow-up.png", eof_disabled=1)
        self.add_action("Move down", self.move_seq_down, icon="arrow-down.png", eof_disabled=1)
        self.add_action("-")

    def move_seq_up(self):
        if self.current_row > 0:
            nr = self.model.get_record(self.current_row - 1)
            cr = self.model.get_record(self.current_row)
            if nr["seq"] == cr["seq"]:
                nr["seq"] = "%s" % (int_(nr["seq"]) - 1)
            else:
                nr["seq"], cr["seq"] = cr["seq"], nr["seq"]
            self.model.update(nr)
            self.model.update(cr)
            self.refresh()
            self.set_grid_index(self.current_row - 1)

    def move_seq_down(self):
        if self.current_row < self.model.row_count() - 1:
            nr = self.model.get_record(self.current_row + 1)
            cr = self.model.get_record(self.current_row)
            if nr["seq"] == cr["seq"]:
                nr["seq"] = "%s" % (int_(nr["seq"]) + 1)
            else:
                nr["seq"], cr["seq"] = cr["seq"], nr["seq"]
            self.model.update(nr)
            self.model.update(cr)
            self.refresh()
            self.set_grid_index(self.current_row + 1)

    def next_sequense(self):
        if self.crud_mode in (NEW, COPY):
            self.s.seq = self.model.cursor.get_next_sequence("seq", num(self.r.seq))
