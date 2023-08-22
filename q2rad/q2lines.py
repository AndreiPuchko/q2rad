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


from q2gui.q2model import Q2CursorModel
from q2rad.q2raddb import Q2Cursor, insert
from q2gui.q2dialogs import q2AskYN
from q2rad.q2utils import choice_table, choice_column, choice_form, Q2_save_and_run


from q2rad.q2utils import Q2Form

from q2gui import q2app


import gettext

_ = gettext.gettext

SQL_DATATYPES = (
    "char",
    "varchar",
    "int",
    "bigint",
    "integer",
    "num",
    "dec",
    "decimal",
    "text",
    "longtext",
    "date",
    "time",
    "datetime",
)
HAS_DATADEC = ("dec", "numeric", "num")
HAS_DATALEN = ("char", "varchar") + HAS_DATADEC
WIDGETS = ("line", "text", "code", "button", "check", "radio", "combo", "list", "spin", "image", "widget")
# "date;"
# "frame;"
# "grid;"
# "label;"
# "lookup;"
# "progressbar;"
# "relation;"
# "space;"
# "tab;"
# "toolbar;"
# "toolbutton;"

HAS_PIC = "radio;" "combo;" "list;"


class Q2Lines(Q2Form, Q2_save_and_run):
    def __init__(self, title=""):
        super().__init__("Lines")
        self.no_view_action = True

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="lines", order="seq")
        model = Q2CursorModel(cursor)
        self.set_model(model)

        self.add_action("/crud")
        # self.add_seq_actions()

        self.add_action("Run", self.form_runner, hotkey="F4")
        self.add_action("Fill", self.filler)

    def create_form(self):
        self.add_control("id", "", datatype="int", pk="*", ai="*", noform=1, nogrid=1)
        self.add_control(
            "name",
            _("Form"),
            # disabled="*",
            to_table="forms",
            to_column="name",
            related="name",
            datatype="char",
            datalen=100
        )
        self.add_control("column", _("Column name"), datalen=50)
        self.add_control("/")
        if self.add_control("/t", _("Main")):
            self.add_control("/f")
            self.add_control("label", _("Form label"), datatype="char", datalen=100)
            self.add_control("gridlabel", _("Grid label"))
            if self.add_control("/h"):
                self.add_control("seq", _("Sequence number"), datatype="int")
                self.add_control("nogrid", _("No grid"), control="check", datalen=1)
                self.add_control("noform", _("No form"), control="check", datalen=1)
                self.add_control("check", _("Has checkbox"), control="check", datalen=1)
                self.add_control("disabled", _("Disabled"), control="check", datalen=1)
                self.add_control("readonly", _("Readonly"), control="check", datalen=1)
                self.add_control("/s")
                self.add_control("/")
            self.add_control("tag", _("Tag"), datatype="char", datalen=100)
            if self.add_control("/h", _("Control type")):

                self.add_control(
                    "control",
                    gridlabel=_("Control type"),
                    pic=";".join(WIDGETS),
                    control="combo",
                    valid=self.control_valid,
                    datatype="char",
                    datalen=15,
                )
                self.add_control("pic", _("Control data"), datatype="char", datalen=250)
                self.add_control("/")

            if self.add_control("/h", _("Data type")):

                self.add_control(
                    "datatype",
                    gridlabel=_("Data type"),
                    pic=";".join(SQL_DATATYPES),
                    control="combo",
                    valid=self.datatype_valid,
                    datatype="char",
                    datalen=15,
                )
                self.add_control("datalen", _("Data length"), datatype="int")
                self.add_control("datadec", _("Decimal length"), datatype="int")
                self.add_control("/s")
                self.add_control("/")

            if self.add_control("/h"):  # Db

                self.add_control(
                    "migrate",
                    _("Migrate"),
                    control="check",
                    valid=self.database_valid,
                    datatype="char",
                    datalen=1,
                )
                self.add_control(
                    "pk",
                    _("Primary key"),
                    control="check",
                    datatype="char",
                    datalen=1,
                    valid=self.database_valid,
                )
                self.add_control(
                    "ai",
                    _("Autoincrement"),
                    control="check",
                    datatype="char",
                    datalen=1,
                    valid=self.database_valid,
                )
                self.add_control("/s")
                self.add_control("/")
            self.add_control("/")  # Linked
            if self.add_control("/f", _("Linked")):
                if self.add_control("/h", _("To table")):
                    self.add_control(
                        "select_table",
                        _("?"),
                        mess=_("Open list of existing tables"),
                        control="button",
                        datalen=3,
                        valid=self.select_linked_table,
                    )
                    self.add_control("to_table", gridlabel=_("To table"), datatype="char", datalen=100)
                    self.add_control("/")
                if self.add_control("/h", _("To field")):
                    self.add_control(
                        "select_pk",
                        _("?"),
                        mess=_("Open list of existing tables"),
                        control="button",
                        datalen=3,
                        valid=self.select_linked_table_pk,
                    )
                    self.add_control("to_column", gridlabel=_("To field"), datatype="char", datalen=100)
                    self.add_control("/")
                if self.add_control("/h", _("Data to show")):
                    self.add_control(
                        "select_column",
                        _("?"),
                        mess=_("Open list of existing columns"),
                        control="button",
                        datalen=3,
                        valid=self.select_linked_table_column,
                    )
                    self.add_control(
                        "related", control="codesql", gridlabel=_("Data to show"), datatype="text"
                    )
                    self.add_control("/")
                if self.add_control("/h", _("Form to open")):
                    self.add_control(
                        "select_form",
                        _("?"),
                        mess=_("Open list of existing forms"),
                        control="button",
                        datalen=3,
                        valid=self.select_linked_form,
                    )
                    self.add_control("to_form", gridlabel=_("Form to open"), datatype="char", datalen=100)
                    self.add_control("/")

                self.add_control("/")

            self.add_control("/s")

        self.add_control("/t", _("Comment"))
        self.add_control("comment", gridlabel=_("Comments"), datatype="longtext")
        self.add_control("/t", _("Script When"))
        self.add_control(
            "code_when",
            _("Script When"),
            control="code",
            nogrid="*",
            datatype="longtext",
        )
        self.add_control("/t", _("Script Show"))
        self.add_control(
            "code_show",
            _("Script When"),
            control="code",
            nogrid="*",
            datatype="longtext",
        )
        self.add_control("/t", _("Script Valid"))
        self.add_control(
            "code_valid",
            _("Script When"),
            control="code",
            nogrid="*",
            datatype="longtext",
        )
        self.add_control("/")
        self._add_save_and_run()
        self._add_save_and_run_visible()

    def before_form_build(self):
        if self._save_and_run_control is None:
            self._save_and_run_control = self.controls.get("save_and_run_actions_visible")
            self.controls.delete("save_and_run_actions_visible")
        self.system_controls.insert(2, self._save_and_run_control)

    def filler(self):
        if self.model.row_count() > 0:
            if q2AskYN("Lines list is not empty! Are you sure") != 2:
                return

        cols = self.q2_app.db_data.db_schema.get_schema_columns(self.prev_form.r.form_table)
        for x in cols:
            insert(
                "lines",
                {
                    "name": self.prev_form.r.name,
                    "column": x,
                    "label": x,
                    "datatype": cols[x]["datatype"],
                    "datalen": cols[x]["datalen"],
                    "pk": cols[x]["pk"],
                    "ai": cols[x]["ai"],
                    "migrate": "*",
                },
                self.db,
            )
        self.refresh()

    def before_crud_save(self):
        if not self.s.migrate:
            self.s.pk = ""
            self.s.ai = ""

    def form_runner(self):
        self.prev_form.run_action("Run")

    def before_form_show(self):
        self.datatype_valid()
        self.control_valid()
        self.database_valid()
        # self.next_sequense()

    def datatype_valid(self):
        self.w.datalen.set_enabled(self.s.datatype in ";".join(HAS_DATALEN))
        self.w.datadec.set_enabled(self.s.datatype in ";".join(HAS_DATADEC))

    def control_valid(self):
        self.w.pic.set_enabled(self.s.control in HAS_PIC)

    def database_valid(self):
        self.w.pk.set_enabled(self.s.migrate)
        self.w.ai.set_enabled(self.s.migrate)
        name = self.prev_form.r.name
        id = self.r.id
        id_where = ""
        if self.crud_mode in ("EDIT", "VIEW"):
            id_where = f" and id <> {id}"
        sql = f"select * from lines where pk='*' and name = '{name}' {id_where}"
        if not self.s.migrate or self.db.cursor(sql).row_count() > 0:
            self.w.pk.set_disabled()
            self.w.ai.set_disabled()

    def select_linked_table(self):
        choice = choice_table()
        if choice:
            self.s.to_table = choice

    def select_linked_table_pk(self):
        if self.s.to_table:
            choice = choice_column(self.s.to_table)
            if choice:
                self.s.to_column = choice

    def select_linked_table_column(self):
        if self.s.to_table:
            choice = choice_column(self.s.to_table)
            if choice:
                self.s.related += ", " if self.s.related else ""
                self.s.related += choice

    def select_linked_form(self):
        choice = choice_form()
        if choice:
            self.s.to_form = choice
