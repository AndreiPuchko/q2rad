if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2gui import q2app
from q2gui.q2form import NEW, COPY
from q2gui.q2model import Q2CursorModel


from q2db.schema import Q2DbSchema
from q2db.db import Q2Db
from q2db.cursor import Q2Cursor

import gettext

from q2rad import Q2App, Q2Form


SQL_ENGINES = ["MySQl", "Sqlite", "Postgresql"]

_ = gettext.gettext


class Q2AppSelect(Q2Form):
    def __init__(self):
        super().__init__(_("Select application"))
        self.selected_application = {}
        self.no_view_action = True
        self.autoload_enabled = True

    def on_init(self):
        q2_app: Q2App = q2app.q2_app
        q2_app.clear_menu()
        q2_app.build_menu()
        q2_app.hide_menubar()
        q2_app.hide_toolbar()
        q2_app.hide_statusbar()
        q2_app.hide_tabbar()

        self.db = Q2Db(database_name="q2apps.sqlite")

        self.define_form()

        data_schema = Q2DbSchema()
        for x in self.get_table_schema():
            data_schema.add(**x)

        self.db.set_schema(data_schema)

    def define_form(self):
        self.add_control("uid", "", datatype="int", pk="*", noform=1, nogrid=1)
        if self.add_control("/h"):
            self.add_control("ordnum", _("Order"), datatype="int")
            self.add_control(
                "autoselect",
                label=_("Autoload"),
                datatype="char",
                datalen=1,
                control="check",
            )
            self.add_control("/")
        self.add_control("name", _("Name"), datatype="char", datalen=100)

        self.add_control("/")
        if self.add_control("/f", _("Data database")):

            def driverDataValid(self=self):
                self.w.host_data.set_enabled(self.s.driver_data != "Sqlite")
                self.w.port_data.set_enabled(self.s.driver_data != "Sqlite")
                self.w.select_database_file.set_enabled(self.s.driver_data == "Sqlite")

            self.add_control(
                "driver_data",
                label=_("Storage type"),
                gridlabel=_("Data storage type"),
                control="radio",
                datatype="char",
                datalen=30,
                pic=";".join(SQL_ENGINES),
                valid=driverDataValid,
            )
            if self.add_control("/h"):

                def openSqliteData():
                    fname = self.q2_app.get_save_file_dialoq(
                        _("data database"), "", _("SQLite (*.sqlite)")
                    )[0]
                    if fname:
                        self.s.database_data = fname

                self.add_control(
                    "database_data",
                    "Database",
                    gridlabel=_("Data database"),
                    datatype="char",
                    datalen=100,
                )
                self.add_control(
                    "select_database_file",
                    _("?"),
                    mess=_("open sqlite database file"),
                    control="button",
                    datalen=3,
                    valid=openSqliteData,
                )
                self.add_control("/")
            if self.add_control("/h"):
                self.add_control(
                    "host_data", _("Host"), gridlabel=_("Data host"), datalen=100
                )
                self.add_control(
                    "port_data", _("Port"), gridlabel=_("Data port"), datatype="int"
                )
                self.add_control(
                    "guest_mode",
                    _("Guest mode"),
                    control="check",
                    datatype="char",
                    datalen=1,
                    mess=_("No database schema changes"),
                )
                self.add_control("/")

            self.add_control("/")

        if self.add_control("/f", _("Logic database")):

            def driverLogicValid(form=self):
                form.w.host_logic.set_enabled(form.s.driver_logic != "Sqlite")
                form.w.port_logic.set_enabled(form.s.driver_logic != "Sqlite")
                form.w.select_logic_file.set_enabled(form.s.driver_logic == "Sqlite")

            self.add_control(
                "driver_logic",
                label=_("Storage type"),
                gridlabel=_("Logic storage type"),
                control="radio",
                datatype="char",
                datalen=30,
                pic=";".join(SQL_ENGINES),
                valid=driverLogicValid,
            )
            if self.add_control("/h"):

                def openSqliteData():
                    fname = self.q2_app.get_save_file_dialoq(
                        _("data database"), ".", _("SQLite (*.sqlite)")
                    )[0]
                    if fname:
                        self.s.database_logic = fname

                self.add_control(
                    "database_logic",
                    "Database",
                    gridlabel="Logic database",
                    datatype="char",
                    datalen=100,
                )
                self.add_control(
                    "select_logic_file",
                    _("?"),
                    mess=_("opend sqlite database file"),
                    control="button",
                    datalen=3,
                    valid=openSqliteData,
                )
                self.add_control("/")
            if self.add_control("/h"):
                self.add_control(
                    "host_logic", _("Host"), gridlabel=_("Logic host"), datalen=100
                )
                self.add_control(
                    "port_logic", _("Port"), gridlabel=_("Logic port"), datatype="int"
                )
                self.add_control("/")

        self.add_action(
            _("Select"),
            self.select_application,
            hotkey="Enter",
            tag="select",
            eof_disabled=1,
        )

        def before_form_show():
            self.w.driver_data.valid()
            self.w.driver_logic.valid()
            if self.crud_mode in [NEW, COPY]:
                self.s.ordnum = self.db.cursor(
                    "select max(ordnum)+1 as mo from applications"
                ).r.mo
                self.w.name.set_focus()

        self.before_form_show = before_form_show

        def before_crud_save():
            if self.s.driver_logic == "2":
                self.s.host_logic = ""
                self.s.port_logic = ""
            if self.s.driver_data == "2":
                self.s.host_data = ""
                self.s.port_data = ""
            if self.s.autoselect:
                self.db.cursor("update applications set autoselect='' ")

            return True

        self.before_crud_save = before_crud_save
        cursor: Q2Cursor = self.db.table(table_name="applications")
        model = Q2CursorModel(cursor)
        model.set_order("ordnum").refresh()
        self.set_model(model)

        self.actions.add_action("/crud")

    def before_grid_show(self):
        self.q2_app.sleep(0.2)
        if self.q2_app.keyboard_modifiers() != "":
            return
        for x in range(self.model.row_count()):
            self.set_grid_index(x)
            if self.r.autoselect:
                if self.autoload_enabled:
                    self._select_application()
                    return False
                break

    def _select_application(self):
        q2_app: Q2App = q2app.q2_app
        q2_app.show_menubar()
        q2_app.show_toolbar()
        q2_app.show_statusbar()
        q2_app.show_tabbar()
        self.selected_application = self.model.get_record(self.current_row)

    def select_application(self):
        self._select_application()
        self.close()

    def run(self, autoload_enabled=True):
        self.autoload_enabled = autoload_enabled
        return super().run()
