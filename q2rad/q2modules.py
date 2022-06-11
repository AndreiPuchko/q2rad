if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2dialogs import q2AskYN
from q2rad import Q2Form

import gettext

from q2gui.q2app import Q2Actions

_ = gettext.gettext


class Q2Modules(Q2Form):
    def __init__(self):
        super().__init__("Modules")
        self.no_view_action = True

    def on_init(self):
        self.editor_actions = Q2Actions()
        self.editor_actions.add_action(
            "Run script", self.editor_script_runner, hotkey="F4"
        )
        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("/")
        self.add_control("/t", "Script")
        self.add_control(
            "script",
            gridlabel=_("Module"),
            control="code",
            nogrid=1,
            actions=self.editor_actions,
        )
        self.add_control("/t", "Comment")
        self.add_control("comment", _("Comment"), datatype="text")

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="modules")
        model = Q2CursorModel(cursor)
        model.set_order("name").refresh()
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("Run", self.script_runner, hotkey="F4")

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
                        % code["error"]
                    )
                )
                != 2
            ):
                return False
        return super().before_crud_save()

    def script_runner(self):
        self.q2_app.code_runner(self.r.script)()

    def editor_script_runner(self):
        self.q2_app.code_runner(self.s.script)()
