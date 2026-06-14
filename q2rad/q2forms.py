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


from q2db.cursor import Q2Cursor

from q2gui.q2model import Q2CursorModel

from q2gui.q2dialogs import q2mess, q2ask
from q2gui import q2app

from q2rad.q2lines import Q2Lines
from q2rad.q2actions import Q2Actions
from q2rad.q2utils import choice_table, choice_form, choice_column, Q2_save_and_run, tr
from q2rad.q2utils import Q2Form, q2cursor


_ = tr


class Q2Forms(Q2Form, Q2_save_and_run):
    def __init__(self, title=_("Forms")):
        super().__init__(title)
        self.no_view_action = True
        self.code_snippets = [
            "after_form_load",
            "before_form_build",
            "before_grid_build",
            "before_grid_show",
            "after_grid_show",
            "grid_index_changed",
            "before_form_show",
            "after_form_show",
            "before_crud_save",
            "after_crud_save",
            "before_delete",
            "form_valid",
            "after_delete",
            "form_refresh",
            "after_form_closed",
        ]
        self.code_snippets_key = 200

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="forms", order="seq")
        model = Q2CursorModel(cursor)
        self.set_model(model)

        self.add_action("/crud")

        self.add_action(
            _("Lines"),
            child_form=Q2Lines,
            child_where="name='{name}'",
            hotkey="F2",
            eof_disabled=1,
        )
        self.add_action(
            _("Actions"),
            child_form=Q2Actions,
            child_where="name='{name}'",
            hotkey="F3",
            eof_disabled=1,
        )

        # self.add_seq_actions()

        self.add_action(_("Migrate"), self.q2_app.migrate_db_data, eof_disabled=1)
        self.add_action(_("Run"), self.form_runner, hotkey="F4", eof_disabled=1, tag="orange")

    def create_form(self):
        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("/")

        if self.add_control("/t", _("Main")):
            self.add_control("/h")
            self.add_control("title", _("Title"), datatype="char", datalen=100)
            self.add_control("seq", _("Sequence number"), datatype="int")
            self.add_control("/s")
            self.add_control("/")
            self.add_control("/f", _("Main menu"))
            self.add_control("menu_path", _("Menu bar path"), datatype="char", datalen=100)
            self.add_control("menu_text", _("Menu text"), datatype="char", datalen=100)
            self.add_control("menu_before", _("Before path"), datatype="char", datalen=100)
            self.add_control("menu_icon", _("Icon file name or char"), datatype="char", datalen=100)
            self.add_control("menu_tiptext", _("Tip text"), datatype="char", datalen=100)
            if self.add_control("/h"):
                self.add_control(
                    "menu_separator",
                    _("Add separator before"),
                    control="check",
                    datatype="char",
                    datalen=1,
                )
                self.add_control(
                    "toolbar",
                    _("Show in app toolbar"),
                    control="check",
                    datatype="char",
                    datalen=1,
                )

                self.add_control("/")
            self.add_control("/")
            self.add_control("/h")
            self.add_control(
                "ok_button",
                _("Add OK button"),
                datatype="char",
                datalen=1,
                control="check",
            )
            self.add_control(
                "cancel_button",
                _("Add Cancel button"),
                datatype="char",
                datalen=1,
                control="check",
            )
            self.add_control(
                "view_action",
                _("Add view actions"),
                datatype="char",
                datalen=1,
                control="check",
            )
            self.add_control("/")

            if self.add_control("/f", _("Data")):
                if self.add_control("/h", _("Data table")):
                    self.add_control(
                        "select_table",
                        _("?"),
                        mess=_("Open list of existing tables"),
                        control="button",
                        datalen=3,
                        valid=self.select_data_storage_table,
                    )
                    self.add_control("form_table", gridlabel=_("Table"), datalen=63)
                    self.add_control("/")
                if self.add_control("/h", _("Sort by")):
                    self.add_control(
                        "select_data_sort_column",
                        _("?"),
                        mess=_("Open column list"),
                        control="button",
                        datalen=3,
                        valid=self.select_table_sort_column,
                    )
                    self.add_control("form_table_sort", "", datatype="char", datalen=100)
                    self.add_control("/")
                self.add_control("/")
            if self.add_control("/h", _("Auto Filter Form")):

                def select_child_form():
                    choice = choice_form()
                    if choice:
                        self.s.filter_form = choice["name"]

                self.add_control(
                    "Select_form",
                    _("?"),
                    mess=_("Open list of existing forms"),
                    control="button",
                    datalen=3,
                    valid=select_child_form,
                )
                self.add_control("filter_form", gridlabel=_("Filter form"), datatype="char", datalen=100)
                self.add_control("lines_per_tab", _("Max lines per tab"), datatype="int")
                self.add_control("/")

            # self.add_control("/s")

        self.add_control("/t", _("Comments"))
        self.add_control("/f")
        self.add_control("comment", gridlabel=_("Comments"), datatype="longtext")

        if self.add_control("/t", _("After load")):
            self.add_control(
                "after_form_load",
                label=_("After Form load"),
                nogrid="*",
                control="code",
            )
        if self.add_control("/t", _("Build")):
            self.add_control("/vs", tag="build")
            self.add_control("/v")
            self.add_control(
                "before_form_build",
                label=_("Before Form Build"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")
            self.add_control("/v")
            self.add_control(
                "before_grid_build",
                label=_("Before Grid Build"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")

        if self.add_control("/t", _("Grid")):
            self.add_control("/vs")
            self.add_control("/v")
            self.add_control(
                "before_grid_show",
                label=_("Before Grid Show"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")
            self.add_control("/v")
            self.add_control(
                "after_grid_show",
                label=_("After Grid Show"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")
            self.add_control("/v")
            self.add_control(
                "grid_index_changed",
                label=_("On Current Row Change"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")

        if self.add_control("/t", _("Form")):
            self.add_control("/vs")
            self.add_control("/v")
            self.add_control(
                "before_form_show",
                label=_("Before Form Show"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")
            self.add_control("/v")
            self.add_control(
                "after_form_show",
                label=_("After Form Show"),
                nogrid="*",
                control="code",
            )
            self.add_control("/")

        if self.add_control("/t", _("Save")):
            self.add_control("/vs")
            self.add_control("/v")
            self.add_control("before_crud_save", label=_("Before save"), nogrid="*", control="code")
            self.add_control("/")
            self.add_control("/v")
            self.add_control("after_crud_save", label=_("After save"), nogrid="*", control="code")
            self.add_control("/")

        if self.add_control("/t", _("Delete")):
            self.add_control("/vs")
            self.add_control("/v")
            self.add_control("before_delete", label=_("Before delete"), nogrid="*", control="code")
            self.add_control("/")
            self.add_control("/v")
            self.add_control("after_delete", label=_("After delete"), nogrid="*", control="code")
            self.add_control("/")

        if self.add_control("/t", _("Valid")):
            self.add_control(
                "form_valid",
                label="",
                nogrid="*",
                control="code",
            )
        if self.add_control("/t", _("Refresh")):
            self.add_control(
                "form_refresh",
                label="",
                nogrid="*",
                control="code",
            )
        if self.add_control("/t", _("After close")):
            self.add_control(
                "after_form_closed",
                label="",
                nogrid="*",
                control="code",
            )
        self.add_control("/")
        self.add_control("q2_time", "Time", datatype="int", noform=1, alignment=7)
        self._add_save_and_run()
        self._add_save_and_run_visible()

    def before_form_show(self):
        self._save_and_run_disable()
        self.restore_editors_state()

    def select_data_storage_table(self):
        choice = choice_table()
        if choice:
            self.s.form_table = choice["table"]
            if self.s.name == "":
                self.s.name = self.s.form_table
            if self.s.title == "":
                self.s.title = self.s.form_table

    def select_table_sort_column(self):
        choice = choice_column(self.s.form_table)
        if choice:
            self.s.form_table_sort += ", " if self.s.form_table_sort else ""
            self.s.form_table_sort += choice["col"]

    def form_runner(self):
        name = self.r.name
        self.q2_app.run_form(name)

    def before_crud_save(self):
        if self.s.name == "":
            q2mess(_("Give me some NAME!!!"))
            self.w.name.set_focus()
            return False
        self.save_editors_state()

    def after_crud_save(self):
        super().after_crud_save()
        if self.crud_mode != "EDIT":
            if self.s.form_table:
                if self.crud_mode == "NEW" or not self.db.get("lines", f"name='{self.s.name}' and pk='*'"):
                    ai = "*" if q2ask("Set AUTOINCREMENT for primary key?") == 2 else ""
                    self.db.insert(
                        "lines",
                        {
                            "name": self.s.name,
                            "column": "id",
                            "control": "line",
                            "noform": "*",
                            "nogrid": "*",
                            "datatype": "int",
                            "migrate": "*",
                            "pk": "*",
                            "ai": ai,
                        },
                    )
                if self.crud_mode == "NEW" or not self.db.get(
                    "actions", f"name='{self.s.name}' and action_mode=1"
                ):
                    self.db.insert(
                        "actions",
                        {
                            "name": self.s.name,
                            "action_mode": "1",
                        },
                    )
                self.refresh()

    def get_autocompletition_list(self):
        acl = super().get_autocompletition_list()
        name = "" if self.crud_mode == "NEW" else self.r.name
        columns = [f"{x['column']} ({x['label']})" for x in q2cursor(
                f"""
                select `column`, label
                from `lines`
                where name = '{name}'
                order by seq
                """,
                q2app.q2_app.db_logic,
            ).records() if not x['column'].startswith("/")]
        for x in columns:
            acl.append(f"form.s.{x}")
            acl.append(f"form.w.{x}")
            acl.append(f"form.c.{x}")
            acl.append(f"form.r.{x}")
        return acl
