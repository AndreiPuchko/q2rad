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
import json

from q2rad import Q2App, Q2Form
from q2rad.q2raddb import q2cursor
from q2rad.q2appmanager import AppManager
from q2rad.q2raddb import open_url


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
        if self.add_control("/f", _("Data storage")):

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
                        _("data storage"), "", _("SQLite (*.sqlite)")
                    )[0]
                    if fname:
                        self.s.database_data = fname

                self.add_control(
                    "database_data",
                    "Database",
                    gridlabel=_("Data storage"),
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

        if self.add_control("/f", _("Logic storage")):

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
                        _("data storage"), ".", _("SQLite (*.sqlite)")
                    )[0]
                    if fname:
                        self.s.database_logic = fname

                self.add_control(
                    "database_logic",
                    "Database",
                    gridlabel="Logic storage",
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

        self.add_action(_("Demo"), self.run_demo)

        self.before_form_show = self.before_form_show
        self.before_crud_save = self.before_crud_save

        cursor: Q2Cursor = self.db.table(table_name="applications")
        model = Q2CursorModel(cursor)
        model.set_order("ordnum").refresh()
        self.set_model(model)

        self.actions.add_action("/crud")

    def before_grid_show(self):
        self.q2_app.sleep(0.2)
        if self.q2_app.keyboard_modifiers() != "":
            return
        if self.autoload_enabled:
            cu = q2cursor("select * from applications where autoselect<>''", self.db)
            if cu.row_count() > 0:
                self._select_application(cu.record(0))
                return False

    def before_crud_save(self):
        if self.s.driver_logic == "2":
            self.s.host_logic = ""
            self.s.port_logic = ""
        if self.s.driver_data == "2":
            self.s.host_data = ""
            self.s.port_data = ""
        if self.s.autoselect:
            self.db.cursor("update applications set autoselect='' ")
        return True

    def before_form_show(self):
        self.w.driver_data.valid()
        self.w.driver_logic.valid()
        if self.crud_mode in [NEW, COPY]:
            self.s.ordnum = self.model.cursor.get_next_sequence("ordnum", self.r.ordnum)
            self.w.name.set_focus()

    def run_demo(self):
        row = {
            "driver_data": "Sqlite",
            "database_data": ":memory:",
            "driver_logic": "Sqlite",
            "database_logic": ":memory:",
        }
        self._select_application(row)
        self.q2_app.migrate_db_logic()

        demo_app_url = "https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/demo_app/demo_app.json"
        data = json.load(open_url(demo_app_url))
        AppManager.import_json_app(data)

        self.q2_app.migrate_db_data()

        demo_data_url = "https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/demo_app/demo_data.json"
        data = json.load(open_url(demo_data_url))
        AppManager.import_json_data(data)

        self.close()

    def _select_application(self, app_data={}):
        q2_app: Q2App = q2app.q2_app
        q2_app.show_menubar()
        q2_app.show_toolbar()
        q2_app.show_statusbar()
        q2_app.show_tabbar()
        q2_app.selected_application = app_data
        q2_app.open_databases()

    def select_application(self):
        self._select_application(self.model.get_record(self.current_row))
        self.close()

    def run(self, autoload_enabled=True):
        self.autoload_enabled = autoload_enabled
        return super().run()
