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

import os
import sys
import random
import string
import threading
import subprocess
import html

from q2rad import Q2Form as _Q2Form
from q2db.cursor import Q2Cursor
from q2rad.q2raddb import num
from decimal import ROUND_HALF_UP
from q2gui.q2model import Q2Model
from q2gui.q2dialogs import q2ask
from q2gui.q2model import Q2CursorModel
from q2gui import q2app
from q2gui.q2dialogs import q2working, q2Mess, q2wait
from q2gui.q2app import Q2Actions
from q2gui.q2app import Q2Controls
from q2gui.q2utils import int_
from q2rad.q2raddb import get, update, insert

import logging
from logging.handlers import TimedRotatingFileHandler

import gettext

import math
from ftplib import FTP


_ = gettext.gettext


def tr(s):
    if q2app.q2app.q2_app:
        return q2app.q2app.q2_app.i18n.tr(s)
    else:
        return s


def round_(number, ndigits=2):
    if ndigits >= 0:
        return num(number).quantize(
            num("1." + "0" * ndigits) if ndigits != 0 else num(0), rounding=ROUND_HALF_UP
        )
    else:
        return round_(num(number) / num(10 ** abs(ndigits)), 0) * num(10 ** abs(ndigits))


class Q2Form(_Q2Form):
    def add_control(
        self,
        column="",
        label="",
        gridlabel="",
        control="",
        pic="",
        data="",
        datatype="char",
        datalen=0,
        datadec=0,
        pk="",
        ai="",
        migrate="*",
        actions=[],
        alignment=-1,
        to_table="",
        to_column="",
        to_form=None,
        related="",
        db=None,
        mask="",
        opts="",
        when=None,
        show=None,
        valid=None,
        changed=None,
        dblclick=None,
        readonly=None,
        disabled=None,
        check=None,
        noform=None,
        nogrid=None,
        widget=None,
        margins=None,
        stretch=0,
        mess="",
        tag="",
        eat_enter=None,
        hotkey="",
        style="",
        **args,
    ):
        if isinstance(to_form, str) and to_form != "":
            to_form = q2app.q2_app.get_form(to_form)
        return super().add_control(
            column,
            label,
            gridlabel,
            control,
            pic,
            data,
            datatype,
            datalen,
            datadec,
            pk,
            ai,
            migrate,
            actions,
            alignment,
            to_table,
            to_column,
            to_form,
            related,
            db,
            mask,
            opts,
            when,
            show,
            valid,
            changed,
            dblclick,
            readonly,
            disabled,
            check,
            noform,
            nogrid,
            widget,
            margins,
            stretch,
            mess,
            tag,
            eat_enter,
            hotkey,
            style,
            **args,
        )

    def grid_print(self):
        from q2rad.q2rad import get_report

        report = get_report(style=get_report().make_style(font_size=q2app.q2_app.q2style.font_size))

        report.data_sets["cursor"] = [
            {"_n_n_n_": x} for x in range(self.model.row_count()) if not self.model.is_hidden(x)
        ]

        detail_rows = report.new_rows()
        detail_rows.rows["role"] = "table"
        detail_rows.rows["data_source"] = "cursor"

        header_rows = report.new_rows(
            style=report.make_style(text_align="center", font_weight="bold", vertical_align="middle")
        )

        columns = self.grid_form.get_controls_list("q2grid")[0].get_columns_settings()

        for pos, x in enumerate(columns):
            columns[pos]["pos"] = pos

        columns = {int(x["data"].split(",")[0]): x for x in columns}
        total_width = 0

        for x in sorted(columns.keys()):
            columns[x]["width"] = int_(columns[x]["data"].split(",")[1])
            columns[x]["cwidth"] = "0"
            total_width += columns[x]["width"]

        page_width = round(total_width / (q2app.q2_app.dpi() / 2.54), 2) + 3

        if page_width < 26:
            page_height = 297 / 210 * page_width
        else:
            page_height = 210 / 297 * page_width

        report.add_page(page_width=page_width, page_height=page_height)

        for x in list(columns.keys()):
            columns[x]["cwidth"] = "%s%%" % round(columns[x]["width"] / total_width * 100, 2)

        for x in sorted(columns.keys()):
            meta_pos = columns[x]["pos"]
            report.add_column(width=columns[x]["cwidth"])
            header_rows.set_cell(0, x, "%s" % columns[x]["name"])
            if self.model.meta[meta_pos].get("num") and not self.model.meta[meta_pos].get("relation"):
                format = "N"
            else:
                format = ""
            # elif mem.model.meta[x].get("datatype") == "date":
            #     format = "D"
            # else:
            detail_rows.set_cell(
                0,
                x,
                "{form.grid_data(_n_n_n_, %s, True)}" % meta_pos,
                style=report.make_style(alignment=self.model.alignments[meta_pos]),
                format=format,
            )

        report.set_data(self, "form")

        detail_rows.set_table_header(header_rows)

        report.add_rows(rows=detail_rows)

        report.run()

    def grid_navigation_actions_hook(self, actions):
        if self.is_grid_updateable():
            actions.add_action(tr(q2app.q2app.ACTION_TOOLS_TEXT) + "|-")
            actions.add_action(
                tr(q2app.q2app.ACTION_TOOLS_TEXT) + "|" + tr("Changelog"),
                self.changelog,
                icon="time",
                eof_disabled=1,
            )

    def changelog(self):
        choice = q2ask(
            tr("Select viewing mode for changelog: only current row or all rows?"),
            buttons=[
                "Cancel",
                "Current row",
                "All",
                "Deleted",
                "Inserted",
                "Updated",
            ],
        )
        if choice < 2:  # Cancel
            return

        pk = self.model.get_meta_primary_key()
        table_name = self.model.get_table_name()

        sql = f"select * from log_{table_name} "
        where = self.model.get_where()
        if choice == 2:  # Row
            sql += f"where {pk} = '{self.r.__getattr__(pk)}'"
        elif choice == 3:  # all
            sql += f" where {where}" if where != "" else ""
        elif choice == 4:  # deleted
            sql += 'where q2_mode = "d"' + (f" and {where}" if where != "" else "")
        elif choice == 5:  # inserted
            sql += 'where q2_mode = "i"' + (f" and {where}" if where != "" else "")
        elif choice == 6:  # updated
            sql += 'where q2_mode = ""' + (f" and {where}" if where != "" else "")

        cu = q2cursor(sql, self.db)
        form = Q2Form(f"Changelog ({self.title})")
        form.db = self.db
        form.add_control("/")
        form.add_control("/h", "-")
        form.add_control("q2_mode", "Mode", datalen=3)
        form.add_control("q2_time", "Time", datalen=10)
        form.add_control("/s")
        form.add_control("/")
        form.add_control("/f")
        form.controls.extend(self.controls)
        form.set_cursor(cu)

        def restore(form=form):
            record = form.get_current_record()
            if q2ask("Are You sure?"):
                if get(table_name, [f"{pk}=%s", record.get(pk)], pk):
                    update(table_name, record)
                else:
                    insert(table_name, record)
                self.refresh()

        form.add_action("Restore row", lambda: restore(form), eof_disabled="*")
        form.run()

    def grid_data_info(self):
        form = Q2Form("Info")
        form.add_control("/")
        form.add_control("/vs")
        form.add_control("/h")
        form.add_control("/f")
        form.add_control("row_count", q2app.GRID_DATA_INFO_ROWS, data=self.model.row_count(), readonly=True)
        form.add_control("order", q2app.GRID_DATA_INFO_ORDER, data=self.model.get_order(), readonly=True)
        form.add_control("where", q2app.GRID_DATA_INFO_FILTER, data=self.model.get_where(), readonly=True)
        form.add_control("/")
        form.add_control(
            "columns",
            q2app.GRID_DATA_INFO_COLUMNS,
            control="list",
            pic=";".join(self.model.columns),
            readonly=True,
        )
        form.add_control("/")

        if q2app.q2_app.dev_mode:
            from q2rad.q2queries import Q2QueryEdit

            form.query_edit = Q2QueryEdit()
            form.query_edit._db = self.db
            form.add_control("ql", "", widget=form.query_edit, nogrid=1, migrate=0)

            def after_form_show():
                query = self.model.get_table_name()
                if not query.strip().lower().startswith("select "):
                    where = self.model.get_where()
                    where = "" if where == "" else f" where {where}"
                    order = self.model.get_order()
                    order = "" if order == "" else f" order by {order}"
                    query = f"select * from {query} {where} {order}"
                form.query_edit.set_content({"queries": {"query": query}})

            form.after_form_show = after_form_show

        form.add_control("/")
        form.run()


class q2cursor(Q2Cursor):
    def __init__(self, sql="", q2_db=None, data=[]):
        if q2_db is None:
            q2_db = q2app.q2_app.db_data
        self._q2_db = q2_db
        super().__init__(q2_db, sql, data=data)
        if q2_db.last_sql_error:
            print(q2_db.last_sql_error)

    def q2form(self):
        form = Q2Form(self.sql)
        form.db = self._q2_db
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


def q2choice(records=[], title="Make your choice", column_title=["Column"]):
    if len(records) == 0:
        return None
    setta = Q2Form(title)
    column = list(records[0].keys())[0]
    if isinstance(column_title, str):
        column_title = [column_title]
    for index, column in enumerate(records[0]):
        setta.add_control(column, column_title[index], datalen=300)
    setta.no_view_action = 1
    model = Q2Model()
    # model.set_records(
    #     [{"table": x} for x in self.q2_app.db_data.db_schema.get_schema_tables()]
    # )
    model.set_records(records)

    setta.set_model(model)
    setta.heap.selected = None
    setta.heap.selected_row = None

    def make_choice():
        setta.heap.selected = setta.r.__getattr__(column)
        setta.heap.selected_row = setta.current_row
        setta.close()

    setta.add_action(
        _("Select"),
        make_choice,
        hotkey="Enter",
        tag="select",
        eof_disabled=1,
    )
    setta.run()
    if setta.heap.selected is not None:
        return setta.model.get_record(setta.heap.selected_row)
    else:
        return None


def choice_table():
    return q2choice(
        [
            {"table": x}
            for x in q2app.q2_app.db_data.db_schema.get_schema_tables()
            if not x.startswith("log_")
        ],
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
    logging.getLogger().setLevel(logging.INFO)


def open_folder(folder):
    if "win32" in sys.platform:
        os.startfile(folder)
    elif "darwin" in sys.platform:
        subprocess.Popen(["open", folder])
    else:
        subprocess.Popen(["xdg-open", folder])


open_document = open_folder


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
    def __init__(self, form_name, mem, lines_per_tab=10, exclude=[], dev=False):
        self.form_name = form_name
        self.mem = mem
        self.filter_columns = []
        self.exclude = exclude
        self.mem.ok_button = True
        self.mem.cancel_button = True
        self.mem.add_ok_cancel_buttons()
        self.lines_per_tab = lines_per_tab
        self.dev = dev
        self.auto_filter()

    def auto_filter(self):
        if len(self.exclude) > 0:
            exclude_columns = " and column not in ("
            exclude_columns += ",".join([f'"{x}"' for x in self.exclude]) + ")"
        else:
            exclude_columns = ""

        cu = q2cursor(
            f"""
                select *
                from `lines`
                where name  = '{self.form_name}'
                    and migrate<>''
                    and (label <>'' or gridlabel <> '')
                    and noform = ''
                    {exclude_columns}
                order by seq
            """,
            self.mem.q2_app.db_logic,
        )

        manual_controls_count = len(self.mem.controls)
        make_tabs = cu.row_count() > self.lines_per_tab
        if not make_tabs:
            self.mem.add_control("/f")
        self.mem.add_control("dev", "Dev", control="button", valid=self._dev)
        for col in cu.records():
            if col["column"] in self.exclude:
                continue
            if make_tabs and cu.current_row() % self.lines_per_tab == 0:
                self.mem.add_control("/t", f"={1 + cu.current_row() // self.lines_per_tab}")
                self.mem.add_control("/f")
            if col["control"] == "text":
                col["control"] = "line"
                col["datatype"] = "char"
            col = Q2Controls.validate(col)
            self.filter_columns.append(cu.r.column)
            if col["datatype"] in ["date"] or (
                col.get("num")
                and col.get("to_form", "") == ""
                and col.get("control", "")
                not in (
                    "radio",
                    "vradio",
                    "list",
                    "combo",
                )
            ):
                self.mem.add_control("/h", cu.r.label, check=1)
                col["label"] = "from"
                co = col["column"]
                col["column"] = co + "____1"
                self.mem.add_control(**col)
                col["label"] = "to"
                col["column"] = co + "____2"
                self.mem.add_control(**col)
                self.mem.add_control("/s")
                self.mem.add_control("/")
            # elif col.get("control", "") == "check":
            #     pass
            else:
                col["label"] = cu.r.label
                col["check"] = 1

                self.mem.add_control(**col)
        self.mem.add_control("/")
        if manual_controls_count > 0:
            for x in range(manual_controls_count):
                self.mem.controls.append(self.mem.controls.pop(0))
        self._valid = self.mem.valid
        self.mem.valid = self.valid

    def _dev(self):
        controls = [
            {
                key: value
                for key, value in x.items()
                if not f"{value}".startswith("<") and key not in ["migrate", "args", "margins", "_control"]
            }
            for x in self.mem.controls
            if not x["column"].startswith("dev")
        ]
        for idx, value in enumerate(controls):
            if value["datatype"] == "text":
                controls[idx]["datatype"] = "char"
                controls[idx]["control"] = "line"
                controls[idx]["datalen"] = "100"
        import json

        json_data = json.dumps(controls, indent=2, ensure_ascii=True)
        where_code = ["where_list = []"]
        for x in self.filter_columns:
            where_code.extend(self.mem.prepare_where(x, dev=True))
        where_code.append("")
        where_code.append('where_string = " and ".join(where_list)')
        where_code.append(f'q2_app.run_form("{self.form_name}", where=where_string)')
        where_code.append("return False")
        f = Q2Form("Dev")
        f.add_control("/v")
        f.add_control("lines", "Lines", control="codejson", data=json_data)
        f.add_control("where", "Where", control="codepython", data="\n".join(where_code))
        f.run()

    def valid(self):
        where = []
        if custom_whr := self._valid():
            where.append(custom_whr)
        for x in self.filter_columns:
            where.append(self.mem.prepare_where(x))
        where_string = " and ".join([x for x in where if x])
        q2app.q2_app.run_form(self.form_name, where=where_string)
        return False


def ftp_upload(files=[], server="", workdir="", login="", password=""):
    chunks = sum([math.ceil(os.path.getsize(x) / 1000) for x in files])
    w = q2wait(chunks)
    connection = FTP(server)
    connection.login(login, password)
    connection.cwd(workdir)

    def send_call_back(w=w):
        def realDo(chunk):
            w.step()

        return realDo

    for x in files:
        localfile = open(x, "rb")
        connection.storbinary(f"STOR {os.path.basename(x)}", localfile, 1024, send_call_back())
        localfile.close()
    connection.quit()
    w.close()
