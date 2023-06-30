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

if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2rad.q2raddb import q2cursor
from q2rad.q2utils import choice_form, choice_column
from q2gui import q2app
from q2rad import Q2Form

import gettext

_ = gettext.gettext


class Q2Actions(Q2Form):
    def __init__(self, title=""):
        super().__init__("Actions")
        self.no_view_action = True

    def on_init(self):
        self.db = q2app.q2_app.db_logic
        self.create_form()

        cursor: Q2Cursor = self.db.table(table_name="actions", order="seq")
        model = Q2CursorModel(cursor)
        self.set_model(model)

        self.add_action("/crud")
        # self.add_seq_actions()
        self.add_action("Run", self.form_runner, hotkey="F4")

    def create_form(self):
        self.add_control("id", "", datatype="int", pk="*", ai="*", noform=1, nogrid=1)
        self.add_control(
            "name",
            _("Form"),
            disabled="*",
            to_table="forms",
            to_column="name",
            related="name",
            # nogrid=1,
            # noform=1,
        )
        self.add_control("action_text", _("Action text"))
        self.add_control("/")
        if self.add_control("/t", _("Main")):
            if self.add_control("/f"):
                self.add_control("seq", _("Sequence number"), datatype="int")

                self.add_control(
                    "action_mode",
                    _("Action mode"),
                    pic="CRUD actions;Single Action;Separator",
                    datatype="int",
                    control="radio",
                    valid=self.action_mode_valid,
                )
                self.add_control("action_mess", _("Action message"), datatype="char", datalen=100)
                self.add_control("action_icon", _("Action icon"), datatype="char", datalen=100)
                self.add_control("action_key", _("Hot key"), datatype="char", datalen=10)
                self.add_control(
                    "eof_disabled",
                    _("Disabled for empty grid"),
                    control="check",
                    datatype="char",
                    datalen=1,
                )
                self.add_control("/")

            if self.add_control("/f", "Child form"):
                if self.add_control("/h", _("Form name")):
                    self.add_control(
                        "Select_child_form",
                        _("?"),
                        mess=_("Open list of existing forms"),
                        control="button",
                        datalen=3,
                        valid=self.select_child_form,
                    )
                    self.add_control("child_form", gridlabel=_("Child form"), datatype="char", datalen=100)
                    self.add_control("/")
                if self.add_control("/h", _("Child where")):
                    self.add_control(
                        "Select_child_fk",
                        _("?"),
                        mess=_("Open list of existing columns"),
                        control="button",
                        datalen=3,
                        valid=self.select_child_foreign_key,
                    )
                    self.add_control("child_where", gridlabel=_("Child where"), datatype="char", datalen=100)
                self.add_control("/")
            self.add_control(
                "child_noshow",
                _("Don't show"),
                control="check",
                datatype="char",
                datalen=1,
            )
            self.add_control(
                "child_copy_mode",
                _("Copy mode"),
                pic=_("Ask;Always;Newer"),
                control="radio",
                datatype="int",
            )

            self.add_control("/s")
        self.add_control("/t", _("Action Script"))
        self.add_control(
            "action_worker",
            gridlabel=_("Action Script"),
            datatype="longtext",
            control="code",
            nogrid="*",
        )
        self.add_control("/t", _("Comment"))
        self.add_control("comment", gridlabel=_("Comments"), datatype="longtext", control="text")

    def form_runner(self):
        self.prev_form.run_action("Run")

    def action_mode_valid(self):
        for x in self.widgets():
            if x.startswith("_"):
                continue
            elif x.startswith("/"):
                continue
            elif not hasattr(self.widgets()[x], "set_disabled"):
                continue
            elif x in ("action_mode", "ordnum", "comment", "seq"):
                continue
            else:
                self.widgets()[x].set_disabled(self.s.action_mode != "2")
        self.w.name.set_enabled(True)

    def select_child_form(self):
        choice = choice_form()
        if choice:
            self.s.child_form = choice
            if self.s.child_where == "":
                parent_pk = q2cursor(
                    f"""select column
                        from lines
                        where name='{self.prev_form.r.name}' and pk='*'
                    """,
                    self.db,
                ).r.column
                self.s.child_where = parent_pk + "={%s}" % parent_pk

    def select_child_foreign_key(self):
        if self.s.child_where.startswith("=") or self.s.child_where == "":
            choice = choice_column(self.s.child_form)
            if choice:
                self.s.child_where = choice + self.s.child_where

    def before_form_show(self):
        self.action_mode_valid()
        # self.next_sequense()
