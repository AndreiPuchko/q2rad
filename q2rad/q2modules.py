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
from q2gui.q2dialogs import q2AskYN
from q2rad import Q2Form
from q2rad.q2utils import Q2_save_and_run
from q2gui.q2utils import num

import gettext

from q2gui.q2app import Q2Actions

_ = gettext.gettext


class Q2Modules(Q2Form, Q2_save_and_run):
    def __init__(self, title=""):
        super().__init__("Modules")
        self.no_view_action = True

    def on_init(self):
        self.editor_actions = Q2Actions()
        self.add_control(
            "name",
            _("Name"),
            datatype="char",
            datalen=100,
            pk="*",
            valid=self.name_valid,
        )
        self.add_control("/")
        self.add_control("/t", "Script")
        self.add_control(
            "script",
            gridlabel=_("Module"),
            datatype="longtext",
            control="code",
            nogrid=1,
        )
        self.add_control("/t", "Comment")
        self.add_control("comment", _("Comment"), control="text", dattype="text")

        self.add_control("last_line", "Last line", datatype="int", noform=1, migrate=1)
        self.add_control("/")

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="modules", order="name")
        model = Q2CursorModel(cursor)
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("Run", self.script_runner, hotkey="F4", eof_disabled=1)
        self._add_save_and_run()
        self._add_save_and_run_visible()
        self.dev_actions.add_action("Just run", self.editor_just_run, hotkey="F5")
        self.dev_actions_visible.add_action("Just run", self.editor_just_run, hotkey="F5")

    def before_form_build(self):
        if self._save_and_run_control is None:
            self._save_and_run_control = self.controls.get("save_and_run_actions_visible")
            self.controls.delete("save_and_run_actions_visible")
        self.system_controls.insert(2, self._save_and_run_control)

    def name_valid(self):
        if self.s.name == "manifest":
            for x in [
                'myapp.app_url = ""',
                'myapp.app_description = ""',
                'myapp.app_title = ""',
            ]:
                if x not in self.s.script:
                    self.s.script = x + "\n" + self.s.script

    def before_crud_save(self):
        code = self.q2_app.code_compiler(self.s.script)
        if code["code"] is False:
            if (
                q2AskYN(
                    _(
                        """
                        Error!
                        Do you want to save it anyway?
                        <br><br>
                        Error explanation:
                        <br>%s
                        """
                        % (code["error"].replace("\n", "<br>").replace(" ", "&nbsp;"))
                    )
                )
                != 2
            ):
                return False
        self.s.last_line = self.w.script.current_line()+1
        # return super().before_crud_save()

    def before_form_show(self):
        self.maximized = True
        self._save_and_run_disable()
        if num(self.s.last_line):
            self.w.script.goto_line(num(self.s.last_line))

    def after_form_show(self):
        if self.crud_mode == "EDIT":
            self.w.script.set_focus()

    def script_runner(self):
        self.q2_app.code_runner(self.r.script)()

    def editor_just_run(self):
        self.q2_app.code_runner(self.s.script)()
        self.w.script.set_focus()
