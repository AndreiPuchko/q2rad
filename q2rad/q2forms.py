if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()


from q2db.cursor import Q2Cursor
from q2db.schema import Q2DbSchema

from q2rad.q2raddb import q2cursor, SeqMover
from q2gui.q2model import Q2CursorModel

# from q2gui.q2utils import int_

from q2gui.q2dialogs import q2Mess
from q2gui import q2app

from q2rad.q2lines import Q2Lines
from q2rad.q2actions import Q2Actions

from q2rad import Q2Form

import gettext

_ = gettext.gettext


class Q2Forms(Q2Form, SeqMover):
    def __init__(self):
        super().__init__("Forms")
        self.no_view_action = True

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="forms", order="seq")
        model = Q2CursorModel(cursor)
        model.set_order("seq").refresh()
        self.set_model(model)

        self.add_action("/crud")

        self.add_action(
            "Lines",
            child_form=Q2Lines,
            child_where="name='{name}'",
            hotkey="F2",
        )
        self.add_action(
            "Actions",
            child_form=Q2Actions,
            child_where="name='{name}'",
            hotkey="F3",
        )

        self.add_seq_actions()

        self.add_action("Migrate to DB", self.q2_app.migrate_db_data)
        self.add_action("Run", self.form_runner, hotkey="F4")

    def create_form(self):
        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("/")

        if self.add_control("/t", _("Main")):
            self.add_control("/h")
            self.add_control("title", _("Title"), datatype="char", datalen=100)
            self.add_control("seq", _("Sequence number"), datatype="int")
            self.add_control("/")
            self.add_control("/f", _("Main menu"))
            self.add_control(
                "menu_path", _("Menu bar path"), datatype="char", datalen=100
            )
            self.add_control("menu_text", _("Menu text"), datatype="char", datalen=100)
            self.add_control(
                "menu_before", _("Before path"), datatype="char", datalen=100
            )
            self.add_control(
                "menu_tiptext", _("Tip text"), datatype="char", datalen=100
            )
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
            self.add_control("/")

            self.add_control("/f", _("Data"))
            if self.add_control("/h", _("Data table")):
                #     def selectTable():
                #         q2Mess(12)
                #     self.add_control("select_table", _("?"),
                #                     mess=_("select table name from list"),
                #                     control="button",
                #                     valid=selectTable)
                self.add_control("form_table", gridlabel=_("Table"))
                self.add_control("/")
            self.add_control(
                "form_table_sort", _("Sort by"), datatype="char", datalen=100
            )
            self.add_control("/")
            self.add_control("/s")

        self.add_control("/t", _("Comment"))
        self.add_control("/f")
        self.add_control("comment", gridlabel=_("Comments"), datatype="bigtext")

        if self.add_control("/t", _("Build")):
            self.add_control("/vs")
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
            self.add_control(
                "before_crud_save", label=_("Before save"), nogrid="*", control="code"
            )
            self.add_control("/")
            self.add_control("/v")
            self.add_control(
                "after_crud_save", label=_("After save"), nogrid="*", control="code"
            )
            self.add_control("/")

        if self.add_control("/t", _("Delete")):
            self.add_control("/vs")
            self.add_control("/v")
            self.add_control(
                "before_delete", label=_("Before delete"), nogrid="*", control="code"
            )
            self.add_control("/")
            self.add_control("/v")
            self.add_control(
                "after_delete", label=_("After delete"), nogrid="*", control="code"
            )
            self.add_control("/")

        if self.add_control("/t", _("Valid")):
            self.add_control(
                "form_valid",
                label=_(""),
                nogrid="*",
                control="code",
            )

    def form_runner(self):
        name = self.r.name
        self.q2_app.run_form(name)

    def before_form_show(self):
        self.next_sequense()
