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

import sys
from q2gui import q2app
from q2gui.q2form import NEW, COPY
from q2gui.q2dialogs import q2mess, q2ask
from q2gui.q2utils import Q2Crypto

from q2db.schema import Q2DbSchema
from q2db.db import Q2Db
from q2db.cursor import Q2Cursor

import gettext
import json
import os

from q2rad import Q2App
from q2rad.q2utils import q2cursor, Q2Form
from q2rad.q2raddb import insert
from q2rad.q2appmanager import AppManager
from q2rad.q2raddb import open_url


SQL_ENGINES = ["MySQL", "SQLite", "PostgreSQL"]

_ = gettext.gettext


class Q2AppSelect(Q2Form):
    def __init__(self, db_file_path="q2apps.sqlite"):
        self.db_file_path = db_file_path
        super().__init__(_("Select application"))
        self.selected_application = {}
        self.no_view_action = True
        self.autoload_enabled = True

    def on_init(self):
        self.db = Q2Db(database_name=self.db_file_path)
        self.define_form()

        data_schema = Q2DbSchema()
        for x in self.get_table_schema():
            data_schema.add(**x)

        self.db.set_schema(data_schema)

    def define_form(self):
        self.add_control("uid", "", datatype="int", pk="*", noform=1, nogrid=1)
        if self.add_control("/h"):
            self.add_control("seq", _("Order"), datatype="int")
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
            self.add_control(
                "driver_data",
                label=_("Storage type"),
                gridlabel=_("Data storage type"),
                control="radio",
                datatype="char",
                datalen=30,
                pic=";".join(SQL_ENGINES),
                valid=self.driver_data_valid,
            )
            if self.add_control("/h"):
                self.add_control(
                    "database_data",
                    "Database",
                    gridlabel=_("Data storage"),
                    datatype="char",
                    datalen=255,
                )
                self.add_control(
                    "select_data_storage_file",
                    _("?"),
                    datalen=3,
                    mess=_("Open Data Storage sqlite database file"),
                    control="button",
                    valid=self.openSqliteDataFile,
                )
                self.add_control("/")
            if self.add_control("/h"):
                self.add_control("host_data", _("Host"), gridlabel=_("Data host"), datalen=100, stretch=90)
                self.add_control("port_data", _("Port"), gridlabel=_("Data port"), datatype="int")
                self.add_control(
                    "guest_mode",
                    _("Guest mode"),
                    control="check",
                    datatype="char",
                    datalen=1,
                    mess=_("No database schema changes"),
                )
                self.add_control("/s", stretch=0)
                self.add_control("/")

            self.add_control("/")

        if self.add_control("/f", _("Logic storage")):
            self.add_control(
                "driver_logic",
                label=_("Storage type"),
                gridlabel=_("Logic storage type"),
                control="radio",
                datatype="char",
                datalen=30,
                pic=";".join(SQL_ENGINES),
                valid=self.driver_logic_valid,
            )
            if self.add_control("/h"):
                self.add_control(
                    "database_logic",
                    "Database",
                    gridlabel="Logic storage",
                    datatype="char",
                    datalen=255,
                )
                self.add_control(
                    "select_app_storage_file",
                    _("?"),
                    datalen=3,
                    mess=_("Open App Storage sqlite database file"),
                    control="button",
                    valid=self.openSqliteDataFile,
                )
                self.add_control("/")
            if self.add_control("/h"):
                self.add_control("host_logic", _("Host"), gridlabel=_("Logic host"), datalen=100, stretch=90)
                self.add_control("port_logic", _("Port"), gridlabel=_("Logic port"), datatype="int")
                self.add_control(
                    "dev_mode",
                    _("Dev mode"),
                    control="check",
                    datatype="char",
                    datalen=1,
                    mess=_("Allow to change App"),
                )
                self.add_control("/s", stretch=0)
                self.add_control("/")
            self.add_control("/")

        if self.add_control("/h", "Database Credentials"):
            self.add_control("epwd", "Credentials settings", control="button", valid=self.show_password_form)
            self.add_control(
                "credhash",
                "Credhash",
                datatype="char",
                datalen=256,
                noform=1,
                nogrid=1,
            )
            self.add_control("/")

        self.add_action(
            _("Select"),
            self.select_application,
            hotkey="Enter",
            tag="select",
            eof_disabled=1,
        )

        self.add_action(
            _("Autoload"),
            self.set_autoload,
            icon="☆",
            mess="Toggle autoload mark",
            eof_disabled=1,
            tag="#4dd0e1",
        )

        if sys.platform == "win32":
            try:
                from q2mysql55_win_local.server import run_test
            except Exception:
                self.add_action(
                    _("Install MySQL"),
                    self.install_mysql,
                    icon="database",
                    mess="Install embedded MySQL server",
                )

        self.add_action(_("Demo"), self.run_demo)

        self.before_form_show = self.before_form_show
        self.before_crud_save = self.before_crud_save

        cursor: Q2Cursor = self.db.table(table_name="applications", order="seq")
        self.set_cursor(cursor)

        self.actions.add_action("/crud")

    def install_mysql(self):
        if q2ask("Install MySQL local server?") == 2:
            q2app.q2_app.pip_install("https://github.com/AndreiPuchko/q2mysql55_win_local")
            q2mess(
                "A local MySQL 5.5 server instance will be available "
                f"on port >={q2app.q2_app.windows_mysql_local_server_default_port}."
            )

    @staticmethod
    def decrypt_creds(pin, credhash):
        creds = Q2Crypto(pin).decrypt(credhash)
        if creds is not None:
            username = creds.split(":")[0]
            password = creds.split(":")[1]
            return username, password
        else:
            return None

    def show_password_form(self):
        username = ""
        password = ""
        if self.crud_mode == "EDIT" and self.s.credhash:
            pin = self.get_pin(self.r.name)
            if pin is None:
                return
            if Q2Crypto(pin).check_pin(self.s.credhash) is None:
                q2mess("Wrong PIN")
                return
            creds = self.decrypt_creds(pin, self.s.credhash)
            if creds is not None:
                username, password = creds
        else:
            pin = ""

        pform = Q2Form("Database credentials")
        pform.add_control("/f", "Username")
        pform.add_control(
            "user1",
            "Enter username",
            datatype="char",
            datalen=100,
            pic="*",
            data=username,
        )
        pform.add_control(
            "user2",
            "Repeat username",
            datatype="char",
            datalen=100,
            pic="*",
            data=username,
        )
        pform.add_control("/")

        pform.add_control("/")
        pform.add_control("/f", "Password")
        pform.add_control(
            "pass1",
            "Enter password",
            datatype="char",
            datalen=100,
            pic="*",
            data=password,
        )
        pform.add_control(
            "pass2",
            "Repeat password",
            datatype="char",
            datalen=100,
            pic="*",
            data=password,
        )
        pform.add_control("/")
        pform.add_control("/f", "Protect credentials with PIN")
        pform.add_control("pin1", "Enter PIN", datatype="char", datalen=10, pic="*", data=pin)
        pform.add_control("pin2", "Repeat PIN", datatype="char", datalen=10, pic="*", data=pin)
        pform.add_control("/")

        def after_form_show():
            pass

        pform.after_form_show = after_form_show

        def valid():
            if (pform.s.user1 or pform.s.user2) and pform.s.user1 != pform.s.user2:
                q2mess("Username mismatch")
                return False
            if (pform.s.pass1 or pform.s.pass2) and pform.s.pass1 != pform.s.pass2:
                q2mess("Password mismatch")
                return False
            if (pform.s.pin1 or pform.s.pin2) and pform.s.pin1 != pform.s.pin2:
                q2mess("PIN mismatch")
                return False
            return True

        pform.valid = valid
        pform.ok_button = 1
        pform.cancel_button = 1
        pform.run()

        if pform.ok_pressed:
            if pform.s.user1 == "" and pform.s.pass1 == "":
                self.s.credhash = ""
            else:
                self.s.credhash = Q2Crypto(pform.s.pin1).encrypt(pform.s.user1 + ":" + pform.s.pass1)

    def get_pin(self, app_name=""):
        pinform = Q2Form("Enter PIN")
        pinform.add_control("/")
        pinform.add_control("/h")
        pinform.add_control("/s")
        pinform.add_control("", "Application:", control="label")
        pinform.add_control(
            "appname", app_name, control="label", style="color:green;font-weight:bold;background:white"
        )
        pinform.add_control("/s")
        pinform.add_control("/")
        pinform.add_control("/f")
        pinform.add_control("pin", "PIN", pic="*")
        pinform.ok_button = 1
        pinform.cancel_button = 1

        # def before_form_show():
        #     pinform.w.appname.set_style_sheet("color:green;font-weight:bold")

        # pinform.before_form_show = before_form_show
        pinform.run()
        if pinform.ok_pressed:
            return pinform.s.pin
        else:
            return None

    def driver_logic_valid(self):
        is_sqlite = self.s.driver_logic.lower() == "sqlite"
        self.w.host_logic.set_enabled(not is_sqlite)
        self.w.port_logic.set_enabled(not is_sqlite)
        self.w.select_app_storage_file.set_enabled(is_sqlite)
        self.credentials_fields_enable()

    def driver_data_valid(self):
        is_sqlite = self.s.driver_data.lower() == "sqlite"
        self.w.host_data.set_enabled(not is_sqlite)
        self.w.port_data.set_enabled(not is_sqlite)
        self.w.select_data_storage_file.set_enabled(is_sqlite)
        self.credentials_fields_enable()

    def credentials_fields_enable(self):
        creds_required = self.s.driver_data.lower() != "sqlite" or self.s.driver_logic.lower() != "sqlite"
        # self.w.credhash.set_enabled(creds_required)
        self.w.epwd.set_enabled(creds_required)

    def set_autoload(self):
        clean_this = self.r.autoselect
        self.db.cursor("update applications set autoselect='' ")
        if not clean_this:
            self.db.cursor("update applications set autoselect='*' where uid=%s" % self.r.uid)
        self.refresh(soft=True)

    def openSqliteDataFile(self):
        fname = self.q2_app.get_save_file_dialoq(
            self.focus_widget().meta.get("mess"),
            ".",
            _("SQLite (*.sqlite);;All files(*.*)"),
            confirm_overwrite=False,
        )[0]
        if fname:
            if "_app_" in self.focus_widget().meta.get("column"):
                self.s.database_logic = fname
            else:
                self.s.database_data = fname

    def before_grid_show(self):
        if self.db.table("applications").row_count() <= 0:
            if not os.path.isdir("databases"):
                os.mkdir("databases")
            insert(
                "applications",
                {
                    "ordnum": 1,
                    "name": "My first app",
                    "driver_data": "SQLite",
                    "database_data": "databases/my_first_app_data_storage.sqlite",
                    "driver_logic": "SQLite",
                    "database_logic": "databases/my_first_app_logic_storage.sqlite",
                    "dev_mode": "",
                },
                self.db,
            )
            self.refresh()
        elif (
            q2cursor("select * from applications where autoselect<>''", self.db).row_count() == 1
        ):  # seek autoload
            for row in range(self.model.row_count()):
                if self.model.get_record(row).get("autoselect"):
                    self.set_grid_index(row)
                    break

    def before_crud_save(self):
        if self.s.name == "":
            q2mess(_("Give me some NAME!!!"))
            self.w.name.set_focus()
            return False
        if self.s.database_data == "":
            q2mess(_("Give me some database!!!"))
            self.w.database_data.set_focus()
            return False
        if self.s.database_logic == "":
            q2mess(_("Give me some database!!!"))
            self.w.database_logic.set_focus()
            return False

        if self.s.driver_logic.lower() == "sqlite":
            self.s.host_logic = ""
            self.s.port_logic = ""
            if not os.path.isdir(os.path.dirname(self.s.database_logic)):
                os.makedirs(os.path.dirname(self.s.database_logic))

        if self.s.driver_data.lower() == "sqlite":
            self.s.host_data = ""
            self.s.port_data = ""
            if not os.path.isdir(os.path.dirname(self.s.database_data)):
                os.makedirs(os.path.dirname(self.s.database_data))

        if self.s.autoselect:
            self.db.cursor("update applications set autoselect='' ")
        return True

    def before_form_show(self):
        if self.crud_mode == "NEW":
            self.s.driver_logic = "SQLite"
            self.s.driver_data = "SQLite"
            self.s.dev_mode = ""
            self.s.database_logic = "databases/_logic"
            self.s.database_data = "databases/_data"
        else:
            self.s.driver_logic = SQL_ENGINES[
                ["mysql", "sqlite", "postgresql"].index(self.r.driver_logic.lower())
            ]
            self.s.driver_data = SQL_ENGINES[
                ["mysql", "sqlite", "postgresql"].index(self.r.driver_data.lower())
            ]

        self.w.driver_data.valid()
        self.w.driver_logic.valid()
        if self.crud_mode in [NEW, COPY]:
            self.s.ordnum = self.model.cursor.get_next_sequence("ordnum", self.r.ordnum)
            self.w.name.set_focus()

    def run_demo(self):
        row = {
            "driver_data": "SQLite",
            "database_data": ":memory:",
            "driver_logic": "SQLite",
            "database_logic": ":memory:",
            "dev_mode": "",
        }
        self._select_application(row)
        self.q2_app.migrate_db_logic(self.q2_app.db_logic)
        self.q2_app.migrate_db_logic(self.q2_app.db_logic)

        demo_app_url = f"{self.q2_app.q2market_url}/demo_app.json"
        demo_data_url = f"{self.q2_app.q2market_url}/demo_data.json"
        response_app = open_url(demo_app_url)
        response_data = open_url(demo_data_url)
        if response_app and response_data:
            self.close()
            AppManager.import_json_app(json.load(response_app))
            self.q2_app.open_selected_app()
            AppManager.import_json_data(json.load(response_data))
        else:
            q2mess(_("Can't to load Demo App"))

    def _select_application(self, app_data={}):
        if app_data.get("credhash"):
            pin = self.get_pin(app_data.get("name", ""))
            if pin is None:
                return False
            creds = self.decrypt_creds(pin, app_data.get("credhash"))
            if creds is None:
                q2mess("Wrong PIN")
                return False
            app_data["username"] = creds[0]
            app_data["password"] = creds[1]
        else:
            app_data["username"] = "q2user"
            app_data["password"] = "q2password"
        q2_app: Q2App = q2app.q2_app
        q2_app.dev_mode = app_data.get("dev_mode")
        q2_app.selected_application = app_data
        q2_app.open_databases()
        q2_app.show_menubar()
        q2_app.show_toolbar()
        q2_app.show_statusbar()
        q2_app.show_tabbar()
        self.q2_app.process_events()
        return True

    def select_application(self):
        # self.close()
        self.q2_app.process_events()
        if self._select_application(self.model.get_record(self.current_row)):
            self.close()

    def run(self, autoload_enabled=True):
        q2_app: Q2App = q2app.q2_app
        q2_app.clear_menu()
        q2_app.build_menu()
        q2_app.hide_menubar()
        q2_app.hide_toolbar()
        q2_app.hide_statusbar()
        q2_app.hide_tabbar()

        self.autoload_enabled = autoload_enabled
        self.q2_app.process_events()
        self.q2_app.sleep(0.1)
        km = self.q2_app.keyboard_modifiers()
        if autoload_enabled and km != "shift":
            cu = q2cursor("select * from applications where autoselect<>''", self.db)
            if cu.row_count() > 0:
                if self._select_application(cu.record(0)):
                    return False
        super().run()
