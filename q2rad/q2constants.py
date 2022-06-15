if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2dialogs import q2AskYN
from q2rad import Q2Form
from q2gui import q2app
import gettext

from q2gui.q2app import Q2Actions

_ = gettext.gettext


class Q2Constants(Q2Form):
    def __init__(self):
        super().__init__("Constants")
        self.no_view_action = True

    def on_init(self):
        self.editor_actions = Q2Actions()
        self.add_control("const_name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("const_text", _("Label"), datatype="char", datalen=250)
        self.add_control("const_value", _("Value"), datatype="text")
        self.add_control("comment", _("Comment"), datatype="text")

        cursor: Q2Cursor = self.q2_app.db_data.table(table_name="constants")
        model = Q2CursorModel(cursor)
        model.set_order("const_name").refresh()
        self.set_model(model)
        self.add_action("/crud")


class q2const:
    def __getattr__(self, __name):
        return q2app.q2_app.db_data.get(
            "constants", f"const_name = '{__name}'", "const_value"
        )

    def __setattr__(self, __name, __value):
        const_name = self.get_const_name(__name)
        if const_name:
            q2app.q2_app.db_data.update(
                "constants", {"const_name": __name, "const_value": __value}
            )
        else:
            q2app.q2_app.db_data.insert(
                "constants", {"const_name": __name, "const_value": __value}
            )

    def get_const_name(self, __name):
        const_name = q2app.q2_app.db_data.get(
            "constants", f"const_name = '{__name}'", "const_name"
        )

        return const_name

    def check(self, const_name="", const_text="", const_value="", comment=""):
        if const_name == "":
            return
        _const_name = self.get_const_name(const_name)
        if not _const_name:
            q2app.q2_app.db_data.insert(
                "constants",
                {
                    "const_name": const_name,
                    "const_value": const_value,
                    "const_text": const_text,
                    "comment": comment,
                },
            )
