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
import os
import random
import string
import threading


if __name__ == "__main__":

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2rad import Q2Form
from q2rad.q2raddb import q2cursor, num
from q2gui.q2model import Q2Model
from q2gui import q2app
from q2gui.q2dialogs import q2working
from q2gui.q2app import Q2Actions
from q2gui.q2app import Q2Controls
from q2gui.q2utils import int_

import logging
from logging.handlers import TimedRotatingFileHandler

import gettext

_ = gettext.gettext


def q2choice(records=[], title="Make your choice", column_title="Column"):
    setta = Q2Form(title)
    column = list(records[0].keys())[0]
    setta.add_control(column, column_title, datalen=300)
    setta.no_view_action = 1
    model = Q2Model()
    # model.set_records(
    #     [{"table": x} for x in self.q2_app.db_data.db_schema.get_schema_tables()]
    # )
    model.set_records(records)

    setta.set_model(model)
    setta.heap.selected = None

    def make_choice():
        setta.heap.selected = setta.r.__getattr__(column)
        setta.close()

    setta.add_action(
        _("Select"),
        make_choice,
        hotkey="Enter",
        tag="select",
        eof_disabled=1,
    )
    setta.run()
    return setta.heap.selected


def choice_table():
    return q2choice(
        [{"table": x} for x in q2app.q2_app.db_data.db_schema.get_schema_tables()],
        title="Select table",
        column_title="Table",
    )


def choice_column(table):
    return q2choice(
        [{"col": x} for x in q2app.q2_app.db_data.db_schema.get_schema_columns(table)],
        title="Select column",
        column_title="Column",
    )


def choice_form():
    return q2choice(
        [
            x
            for x in q2cursor(
                """
                select name
                from forms
                order by name
                """,
                q2app.q2_app.db_logic,
            ).records()
        ],
        title="Select form",
        column_title="Form name",
    )


def set_logging(log_folder="log"):
    if not os.path.isdir(log_folder):
        os.mkdir(log_folder)
    handler = TimedRotatingFileHandler(
        f"{log_folder}/q2.log", when="midnight", interval=1, backupCount=5, encoding="utf-8"
    )
    formatter = logging.Formatter("%(asctime)s-%(name)s: %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler])


class Q2Tasker:
    def __init__(self, title="Working..."):
        self.rez = {}
        self.threads = {}
        self.title = title

    def _worker(self, name):
        self.rez[name] = self.threads[name]["worker"](*self.threads[name]["args"])

    def add(self, worker, *args, name=""):
        if name == "" or name in self.threads:
            name = "".join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(5)
            )
        self.threads[name] = {"worker": worker, "args": args}
        self.threads[name]["thread"] = threading.Thread(target=self._worker, args=(name,))
        self.threads[name]["thread"].start()

    def wait(self):
        def _wait(self=self):
            for name in self.threads:
                self.threads[name]["thread"].join()

        q2working(_wait, self.title)
        return self.rez


class Q2_save_and_run:
    def __init__(self) -> None:
        self.dev_actions = Q2Actions()
        self.dev_actions_visible = Q2Actions()
        self._save_and_run_control = None


    def _add_save_and_run(self: Q2Form, save_only=False):
        self.dev_actions.show_main_button = False
        self.dev_actions.show_actions = False
        self.dev_actions.add_action("Save", worker=self._save, hotkey="F2")
        if save_only is False:
            self.dev_actions.add_action("Save and run", worker=self._save_and_run, hotkey="F4")

        self.add_control(
            "save_and_run_actions",
            "",
            actions=self.dev_actions,
            control="toolbar",
            nogrid=1,
            migrate=0,
        )

    def _add_save_and_run_visible(self: Q2Form, save_only=False):
        self.dev_actions_visible.show_main_button = False
        self.dev_actions_visible.add_action("Save", worker=self._save, hotkey="F2")
        if save_only is False:
            self.dev_actions_visible.add_action("Save and run", worker=self._save_and_run, hotkey="F4")

        self.add_control(
            "save_and_run_actions_visible",
            "",
            actions=self.dev_actions_visible,
            control="toolbar",
            nogrid=1,
            migrate=0,
        )

    def _save(self):
        if self.crud_mode == "EDIT":
            self.crud_save(close_form=False)

    def _save_and_run(self):
        if self.crud_mode == "EDIT":
            self._save()
            self.run_action("Run")

    def _save_and_run_disable(self):
        if self.crud_mode != "EDIT":
            self.dev_actions.set_disabled("Save and run")
            self.dev_actions.set_disabled("Save")


class auto_filter:
    def __init__(self, table, mem):
        self.table = table
        self.mem = mem
        self.fico = []
        self.mem.ok_button = True
        self.mem.cancel_button = True
        self.mem.add_ok_cancel_buttons()

        self.auto_filter()

    def auto_filter(self):
        cu = q2cursor(
            f"""
                select *
                from `lines`
                where name  = '{self.table}'
                    and migrate<>''
                    and (label <>'' or gridlabel <> '')
                order by seq
            """,
            self.mem.q2_app.db_logic,
        )
        self.mem.controls.add_control("/f")
        for col in cu.records():
            col = Q2Controls.validate(col)
            self.fico.append(cu.r.column)

            if col["datatype"] in ["date"] or col.get("num"):
                self.mem.controls.add_control("/h", cu.r.label, check=1)
                col["label"] = "from"
                co = col["column"]
                col["column"] = co + "1"
                self.mem.controls.add_control(**col)
                col["label"] = "to"
                col["column"] = co + "2"
                self.mem.controls.add_control(**col)
                self.mem.controls.add_control("/s")
                self.mem.controls.add_control("/")
            else:
                col["label"] = cu.r.label
                col["check"] = 1
                self.mem.controls.add_control(**col)
        self.mem.valid = self.valid

    def valid(self):
        where = []
        for x in self.fico:
            where.append(self.prepare_where(x))
        where_string = " and ".join([x for x in where if x])
        q2app.q2_app.run_form("sales", where=where_string)
        return False

    def prepare_where(self, column=None, control1=None, control2=None):
        mem_widgets = self.mem.widgets().keys()
        if control1 is None:
            if column in mem_widgets:
                control1 = column
            elif column + "1" in mem_widgets:
                control1 = column + "1"
        if control1 not in mem_widgets:
            return ""

        if not self.mem.w.__getattr__(control1).is_checked():
            return ""

        date_control = self.mem.controls.c.__getattr__(control1)["datatype"] == "date"
        num_control = self.mem.controls.c.__getattr__(control1).get("num")
        control1_value = self.mem.s.__getattr__(control1)
        if control2 is None:
            if control1.endswith("1"):
                control2 = control1[:-1] + "2"
                control2_value = self.mem.s.__getattr__(control2)
            else:
                control2_value = None
        if date_control:
            if control1_value == "0000-00-00":
                control1_value = ""
            if control2_value == "0000-00-00":
                control2_value = ""
        elif num_control:
            control1_value = num(control1_value)
            if control2_value:
                control2_value = num(control2_value)

        if (control1_value and control2_value is None) or control1_value == control2_value:
            if date_control or num_control:
                return f"{column} = '{control1_value}'"
            else:
                return f"{column} like '%{control1_value}%'"
        elif (control1_value and not control2_value) or (control1_value > control2_value):
            return f"{column} >= '{control1_value}'"
        elif not control1_value and control2_value:
            return f"{column} <= '{control2_value}'"
        elif control1_value and control2_value:
            return f"{column} >= '{control1_value}' and {column}<='{control2_value}'"
        return ""


from q2rad.q2rad import get_report


def grid_print(mem):
    self = q2app.q2_app
    form = mem
    report = get_report(style=get_report().make_style(font_size=self.q2style.font_size))

    report.data_sets["cursor"] = [{"_n_n_n_": x} for x in range(mem.model.row_count())]

    detail_rows = report.new_rows()
    detail_rows.rows["role"] = "table"
    detail_rows.rows["data_source"] = "cursor"

    header_rows = report.new_rows(
        style=report.make_style(text_align="center", font_weight="bold", vertical_align="middle")
    )

    columns = mem.grid_form.get_controls_list("q2grid")[0].get_columns_settings()

    for pos, x in enumerate(columns):
        columns[pos]["pos"] = pos

    columns = {int(x["data"].split(",")[0]): x for x in columns}
    total_width = 0

    for x in sorted(columns.keys()):
        columns[x]["width"] = int_(columns[x]["data"].split(",")[1])
        columns[x]["cwidth"] = "0"
        total_width += columns[x]["width"]

    page_width = round(total_width / (self.dpi() / 2.54), 2) + 3

    if page_width < 26:
        page_height = 297 / 210 * page_width
    else:
        page_height = 210 / 297 * page_width

    report.add_page(page_width=page_width, page_height=page_height)

    for x in list(columns.keys()):
        columns[x]["cwidth"] = "%s%%" % round(columns[x]["width"] / total_width * 100, 2)

    for x in sorted(columns.keys()):
        report.add_column(width=columns[x]["cwidth"])
        header_rows.set_cell(0, x, "%s" % columns[x]["name"])
        if mem.model.meta[x].get("num") and not mem.model.meta[x].get("relation"):
            format = "N"
        else:
            format = ""
        # elif mem.model.meta[x].get("datatype") == "date":
        #     format = "D"
        # else:
        detail_rows.set_cell(
            0,
            x,
            "{form.grid_data(_n_n_n_, %s, True)}" % columns[x]["pos"],
            style=report.make_style(alignment=mem.model.alignments[x]),
            format=format,
        )

    report.set_data(form, "form")

    detail_rows.set_table_header(header_rows)

    report.add_rows(rows=detail_rows)

    report.run()
