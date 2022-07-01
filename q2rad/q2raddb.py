if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2utils import int_, num
from q2gui import q2app
from q2gui.q2dialogs import q2Mess

from q2rad import Q2Form
from q2gui.q2form import NEW, COPY

import urllib.request


def open_url(url):
    return urllib.request.urlopen(url)


def read_url(url):
    return open_url(url).read()


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


class SeqMover:
    """create actions for swapping rows in forms, lines, actions"""

    def add_seq_actions(self):
        self.add_action("-")
        self.add_action("🡅", self.move_seq_up)
        self.add_action("🡇", self.move_seq_down)
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
