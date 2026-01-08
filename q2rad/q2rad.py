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
import os
import re
import threading
from packaging import version
import webbrowser
from functools import partial
from zipfile import ZipFile

if __name__ == "__main__":
    sys.path.insert(0, ".")


from q2rad import Q2App
from q2gui.q2dialogs import (  # noqa: F401
    q2Mess,
    q2_mess,
    q2mess,
    q2AskYN,
    Q2WaitShow,
    q2Wait,
    q2working,
    q2wait,
    q2_wait,
    q2_wait_show,
    q2ask,
    q2_ask,
    q2_ask_yn,
    q2askyn,
)
from q2gui.q2model import Q2CursorModel
from q2db.schema import Q2DbSchema
from q2db.db import Q2Db
from q2db.cursor import Q2Cursor
from q2rad.q2actions import Q2Actions
from q2rad.q2raddb import *  # noqa:F403

from q2gui import q2app
from q2rad.q2utils import q2cursor, round_
from q2rad.q2appmanager import AppManager
from q2rad.q2stylesettings import AppStyleSettings
from q2terminal.q2terminal import Q2Terminal
from q2rad.q2appselector import Q2AppSelect
from q2rad.q2modules import Q2Modules
from q2rad.q2forms import Q2Forms
from q2rad.q2lines import Q2Lines
from q2rad.q2market import Q2Market
from q2rad.q2packages import Q2Packages
from q2rad.q2extensions import Q2Extensions
from q2rad.q2constants import Q2Constants, q2const
from q2rad.q2queries import Q2Queries
from q2rad.q2reports import Q2Reports, Q2RadReport
from q2rad.q2utils import Q2Tasker, Q2Form, auto_filter, set_logging, open_folder, open_document  # noqa F401
from q2rad.q2utils import q2choice
from q2rad.q2make import make_binary

from q2data2docx.q2data2docx import q2data2docx  # noqa F401

# from q2googledrive.q2googledrive import q2googledrive # noqa F401

import gettext

import json
import subprocess
import shutil
from importlib.metadata import version as version2
from importlib.metadata import distributions
import logging
import traceback


# TODO: excel custom format 2 report


q2_modules = ["q2rad", "q2gui", "q2db", "q2report", "q2terminal", "q2data2docx"]
const = q2const()
_ = gettext.gettext


set_logging()
_logger = logging.getLogger(__name__)


class ReturnEvent(Exception):
    pass


def get_report(report_name="", style={}):
    if report_name == "":
        return Q2RadReport(style=style)
    content = q2app.q2_app.db_logic.get("reports", f"name='{report_name}'", "content")
    if content:
        return Q2RadReport(content)
    else:
        q2Mess(f"Report not fount: {report_name}")
        return None


def run_form(form_name, order="", where=""):
    return q2app.q2_app.run_form(form_name, order=order, where=where)


def get_form(form_name, order="", where=""):
    return q2app.q2_app.get_form(form_name, order=order, where=where)


def run_module(module_name=None, _globals={}, _locals={}, script="", import_only=False):
    ext_modules = []
    if module_name is not None:
        script = q2app.q2_app.db_logic.get("modules", f"name = '{module_name}'", "script")
        for row in q2cursor("select prefix from extensions order by seq").records():
            ext_module_name = row["prefix"] + module_name
            if get("modules", f"name='{ext_module_name}'", "name", q2app.q2_app.db_logic) == ext_module_name:
                ext_modules.append(ext_module_name)
    if get("modules", f"name='_{module_name}'", "name", q2app.q2_app.db_logic) == f"_{module_name}":
        ext_modules.append(f"_{module_name}")
    if script:
        code = q2app.q2_app.code_compiler(script)
        if code["code"] is False:
            msg = code["error"]
            if threading.current_thread() is threading.main_thread():
                q2Mess(f"{msg}".replace("\n", "<br>").replace(" ", "&nbsp;"))
            print(f"{msg}")
            print("-" * 25)
            _logger.error(msg)
            return
        else:
            if import_only:
                __name__ = ""
            else:
                __name__ = "__main__"

            _globals.update(globals())
            _globals.update(
                {
                    "RETURN": None,
                    "ReturnEvent": ReturnEvent,
                    "self": q2app.q2_app,
                    "q2_app": q2app.q2_app,
                    "myapp": q2app.q2_app,
                    "__name__": __name__,
                }
            )
            try:
                if _locals:
                    exec(code["code"], _globals, _locals)
                else:
                    exec(code["code"], _globals)
            except ReturnEvent as error:
                if _locals:
                    _globals["RETURN"] = _locals["RETURN"]
                pass
            except Exception as error:
                explain_error()

    if ext_modules:
        res = None
        for mdl in ext_modules:
            res = run_module(mdl, _globals=_globals, _locals=_locals, import_only=import_only)

        if res is not None:
            return res
    res = _globals.get("RETURN")
    if "RETURN" in _globals:
        del _globals["RETURN"]
    return res


def explain_error(tb=None, errtype=None):
    error = {}
    stack = []
    if tb is None:
        tb = sys.exc_info()[2]
        errtype = sys.exc_info()[1]
        while tb.tb_next:
            stack.append([tb.tb_frame.f_lineno, tb.tb_frame.f_code.co_filename])
            tb = tb.tb_next
    line_no = tb.tb_frame.f_lineno
    err_char = "█"
    if tb.tb_frame.f_code.co_filename.startswith("<"):
        script = tb.tb_frame.f_code.co_filename[1:-1].split("\n")
        if line_no - 1 < len(script):
            errline = script[line_no - 1]
            script[line_no - 1] = (
                f"{err_char * 10}\n{err_char * 2}" + script[line_no - 1] + f"\n{err_char * 10}"
            )
            error["script"] = "\n".join(script)
        else:
            errline = traceback.format_tb(tb)[-1]
            error["script"] = ""
    else:
        errline = ""
        error["script"] = "<br>".join(traceback.format_tb(tb))

    error["errtype"] = errtype
    error["lineno"] = tb.tb_frame.f_lineno
    error["errline"] = errline

    error["locals"] = dict(tb.tb_frame.f_locals)
    stack.reverse()
    error["stack"] = stack

    msg = []
    msg.append("Runtime error:")
    msg.append(str(error["errtype"]))
    msg.append(f"Line:{error['lineno']}:{errline}")
    msg.append("Code:")
    msg.append("-" * 25)
    msg.append(error["script"])
    msg.append("-" * 25)
    msg.append("Local variables:")
    for x in error["locals"]:
        if x in ("RETURN", "ReturnEvent", "mem", "self", "q2_app", "form", "myapp", "__name__"):
            continue
        # if x in globals():
        #     continue
        value = str(error["locals"][x])[:100]
        msg.append(f"{x}: {value}")
    msg.append("-" * 25)
    msg = "\n".join(msg)

    print("-" * 25)
    print(f"{msg}")
    print("-" * 25)
    _logger.error(msg)
    if threading.current_thread() is threading.main_thread():
        q2Mess(f"""{msg}""".replace("\n", "<br>").replace(" ", "&nbsp;").replace("\t", "&nbsp;" * 4))
    return msg


class Q2RadApp(Q2App):
    def __init__(self, title=""):
        _logger.info("About to start")
        super().__init__(title)
        self.settings_title = "q2RAD"
        self.style_file = "q2rad.qss"
        self.frozen = getattr(sys, "frozen", False)
        self.windows_mysql_local_server = None
        self.windows_mysql_local_server_default_port = 3366
        self.windows_mysql_local_server_port = 3366
        self.windows_mysql_local_server_datadir = "mysql_local_databases"
        self.db = None
        self.binary_build = ""
        self.binary_url = ""

        self.db_data = None
        self.db_logic = None
        self.last_root_password = ""
        self.selected_application = {}
        self.q2style.font_size = int_(self.settings.get("Style Settings", "font_size", "10"))  # noqa F405
        self.q2style.font_name = self.settings.get("Style Settings", "font_name", "Arial")  # noqa F405
        self.set_color_mode(self.settings.get("Style Settings", "color_mode", ""))

        self.clear_app_info()

        self.q2market_path = "../q2market"

        # self.dev_mode = os.path.isdir(self.q2market_path)
        self.dev_mode = False

        self.q2market_url = "https://raw.githubusercontent.com/AndreiPuchko/q2market/main/"

        self.assets_url = "https://raw.githubusercontent.com/AndreiPuchko/q2gui/main/assets/"

        # if os.path.isfile(qss_file):
        #     self.style_file = qss_file
        #     self.set_style_sheet()

        self.set_icon("assets/q2rad.ico")

        self.const = const

        sys.excepthook = self.handle_error

    def handle_error(self, exc_type, exc_value, exc_traceback):
        _logger.error(f"{exc_value}")
        explain_error(exc_traceback, exc_value)

    def clear_app_info(self):
        self.app_url = None
        self.app_title = ""
        self.app_version = ""
        self.app_description = ""

    def make_desktop_shortcut(self):
        if sys.platform == "win32":
            subprocess.check_call(["cscript", "make_shortcut.vbs"], shell=True)
        else:
            basepath = os.path.abspath(".")
            desktop_entry = [
                "[Desktop Entry]\n"
                "Name=q2rad\n"
                f"Exec={basepath}/q2rad/bin/q2rad\n"
                f"Path={basepath}\n"
                f"Icon={basepath}/assets/q2rad.ico\n"
                "Terminal=false\n"
                "Type=Application\n"
            ]

            desktop = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
            open(f"{desktop}/q2rad.desktop", "w").writelines("\n".join(desktop_entry))

    def on_start(self):
        if not os.path.isfile("poetry.lock"):
            self.load_assets()
            self.check_packages_update()
        self.install_binary_build()
        self.open_application(autoload_enabled=True)

    def install_binary_build(self):
        if self.frozen and self.binary_url:
            _new_binary_build = read_url(f"{self.binary_url}.ver").decode("utf8")
            if _new_binary_build > self.binary_build:
                if (
                    q2ask(
                        _(
                            "A new version is available.<br>"
                            + ("Current build <b>%s</b><br>" % self.binary_build)
                            + ("new build <b>%s</b><br>" % _new_binary_build)
                            + "Install the new version now?"
                        )
                    )
                    == 2
                ):
                    shutil.rmtree("_new_build", ignore_errors=True)
                    os.makedirs("_new_build", exist_ok=True)
                    new_build_content = read_url(f"{self.binary_url}.exe", waitbar=True)
                    new_build_file_path = os.path.join("_new_build", "new_build.exe")
                    open(new_build_file_path, "wb").write(new_build_content)
                    subprocess.Popen(
                        [new_build_file_path, f"-shortcut-name={self.app_title}", "."],
                        creationflags=subprocess.CREATE_NEW_CONSOLE,
                    )
                    self.close()

    def subwindow_count_changed(self):
        if super().subwindow_count_changed() == 0:
            self.enable_menu("File|Open")
        else:
            self.disable_menu("File|Open")

    def on_new_tab(self):
        if self.db_logic is not None:
            run_module("on_new_tab")

    def open_application(self, autoload_enabled=False):
        self.selected_application = {}
        self.set_title("Open Application")
        Q2AppSelect().run(autoload_enabled)
        if self.selected_application != {}:
            self.open_selected_app(True, migrate_db_data=True)
            if self.check_app_update() or self.check_ext_update():
                self.open_selected_app()
            self.on_new_tab()
        else:
            self.close()
        self.subwindow_count_changed()

    def start_local_mysql(self):
        if self.windows_mysql_local_server is None and sys.platform == "win32":
            try:
                from q2mysql55_win_local.server import Q2MySQL55_Win_Local_Server

                self.windows_mysql_local_server = Q2MySQL55_Win_Local_Server()
                self.windows_mysql_local_server_port = self.windows_mysql_local_server.start(
                    self.windows_mysql_local_server_port, self.windows_mysql_local_server_datadir
                )
            except Exception:
                self.windows_mysql_local_server = None
        if self.windows_mysql_local_server and self.windows_mysql_local_server.is_running():
            _logger.info(
                f"The local MySQl 5.5 server is running on port {self.windows_mysql_local_server.port}"
            )
            if num(self.windows_mysql_local_server.port) != num(self.windows_mysql_local_server_default_port):
                if num(self.selected_application["port_logic"]) == num(
                    self.windows_mysql_local_server_default_port
                ):
                    self.selected_application["port_logic"] = self.windows_mysql_local_server.port
                if num(self.selected_application["port_data"]) == num(
                    self.windows_mysql_local_server_default_port
                ):
                    self.selected_application["port_data"] = self.windows_mysql_local_server.port

    def stop_local_mysql(self):
        if self.windows_mysql_local_server:
            self.windows_mysql_local_server.stop(timeout=0)
            _logger.info("The local MySQL 5.5 server has terminated.")

    def open_selected_app(self, go_to_q2market=False, migrate_db_data=True):
        wait = Q2WaitShow(5, "Loading app> ")
        wait.step("Prepare")
        self.clear_app_info()
        wait.step("Migrate logic DB")
        self.migrate_db_logic(self.db_logic)
        if migrate_db_data:
            wait.step("Migrate data DB")
            self.migrate_db_data()
        else:
            wait.step("Create menus")
            self.create_menu()
        wait.step("looking for updates")
        self.process_events()
        wait.step("Done!")
        wait.close()
        self.update_app_packages()

        self.run_module("manifest")
        self.run_module("version")
        if self.app_title:
            self.set_title(f"{self.app_title}({self.selected_application.get('name', '')})")
        else:
            self.set_title(f"{self.selected_application.get('name', '')}")
        self.run_module("autorun")
        self.run_module("_autorun")

        if go_to_q2market and (
            max(
                [
                    self.db_logic.table("forms").row_count(),
                    self.db_logic.table("lines").row_count(),
                    self.db_logic.table("actions").row_count(),
                    self.db_logic.table("reports").row_count(),
                    self.db_logic.table("modules").row_count(),
                    self.db_logic.table("queries").row_count(),
                    self.db_logic.table("packages").row_count(),
                ]
            )
            <= 0
        ):
            if q2AskYN("Application is empty! Would you like to download some App?") == 2:
                Q2Market().run()

    def migrate_db_data(self):
        data_schema = Q2DbSchema()
        cu = q2cursor(
            """
                select
                    forms.form_table as `table`
                    , `lines`.column
                    , `lines`.datatype
                    , `lines`.datalen
                    , `lines`.datadec
                    , `lines`.to_table
                    , `lines`.to_column
                    , `lines`.related
                    , `lines`.ai
                    , `lines`.pk
                from `lines`, forms
                where forms.name = `lines`.name
                    and form_table <>'' and migrate <>''
                order by forms.seq, `lines`.seq, forms.name
                """,
            self.db_logic,
        )
        for column in cu.records():
            data_schema.add(**column)
        for form in (
            Q2Constants(),
            Q2Extensions(),
        ):
            for x in form.get_table_schema():
                data_schema.add(**x)

        self.db_data.set_schema(data_schema)
        if self.db_data.migrate_error_list:
            q2Mess(self.db_data.migrate_error_list)
        self.create_menu()

    def migrate_db_logic(self, db_logic):
        data_schema = Q2DbSchema()
        for form in (
            Q2Modules(),
            Q2Forms(),
            Q2Lines(),
            Q2Queries(),
            Q2Actions(),
            Q2Reports(),
            Q2Packages(),
        ):
            for x in form.get_table_schema():
                data_schema.add(**x)
        db_logic.set_schema(data_schema)

        data_schema = Q2DbSchema()
        for form in (
            Q2Constants(),
            Q2Extensions(),
        ):
            for x in form.get_table_schema():
                data_schema.add(**x)

        self.db_data.set_schema(data_schema)

    def get_autocompletition_list(self):
        rez = []
        tables = self.db_data.db_schema.get_schema_tables()
        for ta in tables:
            rez.append(ta)
            rez.append(f"d.{ta}")
            for co in tables[ta]["columns"]:
                rez.append(f"d.{ta}.{co}")
                rez.append(f"{ta}.{co}")
        for x in q2cursor("select const_name from  constants").records():
            rez.append("c.const.{const_name}".format(**x))
            rez.append("const.{const_name}".format(**x))
        return rez

    def get_db_admin_credential(self, name="", engine="", host="", port="", rootuser=""):
        ac = Q2Form("Enter database admin credential")
        ac.add_control("name", _("Database name"), data=name, disabled=1)
        ac.add_control("engine", _("Engine"), data=engine, disabled=1)
        ac.add_control("host", _("Host"), data=host, disabled=1)
        ac.add_control("host", _("Port"), data=port, disabled=1)
        ac.add_control("user", _("User name"), data=rootuser)
        ac.add_control("password", _("Password"), pic="*", data=self.last_root_password)
        ac.ok_button = 1
        ac.cancel_button = 1
        ac.after_form_show = lambda: ac.w.password.set_focus()
        ac.run()
        if ac.ok_pressed:
            self.last_root_password = ac.s.password
            return (ac.s.user, ac.s.password)

    def _open_database(self, database_name, db_engine_name, host, port, password, user, guest_mode=None):
        db = None
        first_pass = 0
        while True:
            try:
                db = q2working(
                    lambda: Q2Db(
                        database_name=database_name,
                        db_engine_name=db_engine_name,
                        host=host,
                        port=port,
                        guest_mode=guest_mode,
                        user=user,
                        password=password,
                    ),
                    mess=_("Opening database"),
                )
            except Exception:
                pass
            if first_pass != 0 or db is not None:
                return db
            first_pass += 1
            if db is None:
                credential = self.get_db_admin_credential(
                    database_name, db_engine_name, host, port, Q2Db.get_default_admin_name(db_engine_name)
                )
                if credential is None:
                    return
                else:
                    root_user, root_password = credential
                try:
                    q2working(
                        lambda: Q2Db(
                            database_name=database_name,
                            db_engine_name=db_engine_name,
                            host=host,
                            port=port,
                            guest_mode=guest_mode,
                            user=user,
                            password=password,
                            root_user=root_user,
                            root_password=root_password,
                            create_only=True,
                        ),
                        mess=_("Creating database"),
                    )
                except Exception as error:
                    q2mess(f"Error occured while creating the database:<br>{error}")
                    return None

    def open_databases(self):
        self.start_local_mysql()
        self.db_data = self._open_database(
            database_name=self.selected_application.get("database_data", ""),
            db_engine_name=self.selected_application.get("driver_data", "").lower(),
            host=self.selected_application.get("host_data", ""),
            port=self.selected_application.get("port_data", ""),
            guest_mode=self.selected_application.get("guest_mode", ""),
            user=self.selected_application.get("username", ""),
            password=self.selected_application.get("password", ""),
        )
        self.db = self.db_data
        if self.db_data:
            self.db_logic = self._open_database(
                database_name=self.selected_application.get("database_logic", ""),
                db_engine_name=self.selected_application.get("driver_logic", "").lower(),
                host=self.selected_application.get("host_logic", ""),
                port=self.selected_application.get("port_logic", ""),
                user=self.selected_application.get("username", ""),
                password=self.selected_application.get("password", ""),
            )
        self.last_root_password = ""
        if self.db_data is None or self.db_logic is None:
            self.selected_application = {}
            # q2Mess(_("Can not open database"))
            self.open_application()

    def create_menu(self):
        self.clear_menu()
        self.add_menu("File|About", self.about, icon="info.png")
        self.add_menu("File|Manage", self.run_app_manager, icon="tools.png")
        self.add_menu("File|Style", self.run_stylesettings)
        self.add_menu("File|Constants", self.run_constants)
        if not self.frozen:
            self.add_menu("File|-")
            self.add_menu("File|Open", self.open_application, icon="open.png")
        self.add_menu("File|-")
        self.add_menu("File|Close", self.close, toolbar=1, icon="exit.png")

        self.create_form_menu()

        if self.frozen:
            self.dev_mode = False

        self.dev_mode = (
            self.selected_application.get("dev_mode")
            or os.path.isdir(self.q2market_path)
            or os.path.isfile(".dev")
        )
        # self.dev_mode = False

        if self.dev_mode:
            self.add_menu("Dev|Forms", self.run_forms)
            self.add_menu("Dev|Modules", self.run_modules)
            self.add_menu("Dev|Queries", self.run_queries)
            self.add_menu("Dev|Reports", self.run_reports)
            self.add_menu("Dev|Packages", self.run_packages)
            self.add_menu("Dev|-")
            self.add_menu("Dev|Finder", self.run_finder)
            self.add_menu("Dev|-")
            self.add_menu("Dev|Documentation", self.read_the_docs)
            if not self.frozen:
                self.add_menu("Dev|-")
                self.add_menu("Dev|Make binary", self.make_binary)
        self.build_menu()
        # self.show_toolbar(False)
        pass

    def about(self, text=""):
        about = []
        if self.app_title:
            about.append(f"<b><font size=+1>{self.app_title}</font></b>")
        if self.app_description:
            about.append(f"<i>{self.app_description}</i>")
        if self.app_version:
            about.append(f"Uploaded: {self.app_version}")
        if self.app_url:
            about.append(f"URL: <u>{self.app_url}</u>")
        about.append("")
        if self.binary_build:
            about.append(f"Binary build: {self.binary_build}")
        about.append("")
        if text:
            about.append(text)
        about.append(f"<b>Python</b>: {sys.version}<p>")

        if not self.frozen:
            about.append("Versions:")
            about.append("<b>q2RAD</b>")
            rez = self.get_packages_version(q2_modules)

            for package in rez:
                latest_version, current_version = rez[package]
                if latest_version:
                    if current_version != latest_version:
                        latest_version_text = f"({latest_version})"
                    else:
                        latest_version_text = ""
                else:
                    latest_version_text = _(" (Can't load package info)")

                about.append(f"<b>{package}</b>: {current_version}{latest_version_text}")

        q2Mess("<br>".join(about))

    def asset_file_loader(self, name):
        if name.endswith(".svg"):
            asset_url = f"https://unpkg.com/lucide-static@latest/icons/{name}"
        else:
            asset_url = f"{self.assets_url}/{name}"
        try:
            asset_content = read_url(asset_url)  # noqa F405
            if not asset_content:
                _logger.info(f"Asset not found {asset_url}")
                return False
        except Exception:
            _logger.info(f"Error reading {asset_url}")
            return False

        try:
            open(f"assets/{name}", "wb").write(asset_content)
            return True
        except Exception:
            _logger.info(f"Error writing asset/{name}")
            return False

    def write_restore_file(self, name, content):
        if sys.platform == "win32":
            u_file = open(f"{name}.bat", "w")
        else:
            u_file = open(os.open(f"{name}.sh", os.O_CREAT | os.O_WRONLY, 0o777), "w")
        u_file.write(content)
        u_file.close()

    def load_assets(self, force_reload=False):
        if os.path.isdir("assets") and force_reload is False:
            return
        if not os.path.isdir("assets"):
            os.mkdir("assets")
        # first run
        # load icons
        icons = [getattr(q2app, x) for x in dir(q2app) if x.endswith("ICON") and getattr(q2app, x) != ""]
        icons.append("q2gui.ico")

        errors = []

        tasker = Q2Tasker("Downloading assets...")
        for x in icons:
            tasker.add(self.asset_file_loader, x, name=x)
        rez = tasker.wait()

        for x in icons:
            if rez[x] is False:
                errors.append(x)

        if os.path.isfile("assets/q2gui.ico"):
            shutil.copyfile("assets/q2gui.ico", "assets/q2rad.ico")

        if errors:
            q2Mess(_("<b>Loading failed for</b>:<br>") + "<br>".join(errors))
            return

        self.set_icon("assets/q2rad.ico")

        if os.path.isfile("poetry.lock"):
            return

        if not self.frozen:
            # create update_q2rad.sh
            self.write_reinstall_files()

            # create run_q2rad
            self.write_run_files()
            if sys.platform != "darwin":
                if q2AskYN("Should I make a desktop shortcut?") == 2:
                    self.make_desktop_shortcut()
        self.process_events()

    def write_run_files(self):
        if sys.prefix != sys.base_prefix:  # in virtualenv
            self.write_restore_file(
                "run_q2rad",
                ("" if "win32" in sys.platform else "#!/bin/bash\n")
                + (
                    "start q2rad\\scripts\\pythonw.exe -m q2rad"
                    if "win32" in sys.platform
                    else "q2rad/bin/q2rad\n"
                ),
            )
        elif os.path.isdir(f"python.loc.{sys.version.split()[0]}"):
            self.write_restore_file(
                "run_q2rad",
                ("" if "win32" in sys.platform else "#!/bin/bash\n")
                + (
                    f"python.loc.{sys.version.split()[0]}\\scripts\\q2rad"
                    if "win32" in sys.platform
                    else f"python.loc.{sys.version.split()[0]}/bin/q2rad\n"
                ),
            )
        else:
            self.write_restore_file(
                "run_q2rad",
                ("" if "win32" in sys.platform else "#!/bin/bash\n")
                + ("pythonw.exe -m q2rad" if "win32" in sys.platform else "python -m q2rad\n"),
            )

        if "win32" in sys.platform:
            if os.path.isdir(f"python.loc.{sys.version.split()[0]}"):
                open("run_q2rad.vbs", "w").write(
                    'WScript.CreateObject("WScript.Shell").Run '
                    f'"python.loc.{sys.version.split()[0]}\\pythonw.exe -m q2rad", 1, false'
                )
            else:  # venv
                open("run_q2rad.vbs", "w").write(
                    'WScript.CreateObject("WScript.Shell").Run '
                    '"q2rad\\scripts\\pythonw.exe -m q2rad", 1, false'
                )

            open("make_shortcut.vbs", "w").write(
                'Set oWS = WScript.CreateObject("WScript.Shell")\n'
                'Set oLink = oWS.CreateShortcut(oWS.SpecialFolders("Desktop") & "\\q2RAD.lnk")\n'
                'cu = WScript.CreateObject("Scripting.FileSystemObject").'
                "GetParentFolderName(WScript.ScriptFullName)\n"
                'oLink.TargetPath = cu & "\\run_q2rad.vbs"\n'
                'oLink.WorkingDirectory = cu & ""\n'
                'oLink.Description = "q2RAD"\n'
                'oLink.IconLocation = cu & "\\assets\\q2rad.ico"\n'
                "oLink.Save\n"
            )

    def write_reinstall_files(self):
        if sys.prefix != sys.base_prefix:  # in virtualenv
            pip_command = "q2rad\\scripts\\python -m " if "win32" in sys.platform else "q2rad/bin/python -m "
        elif os.path.isdir(f"python.loc.{sys.version.split()[0]}"):
            pip_command = (
                f"python.loc.{sys.version.split()[0]}\\python  -m "
                if "win32" in sys.platform
                else f"python.loc{sys.version.split()[0]}/python -m "
            )
        else:
            pip_command = "python  -m " if "win32" in sys.platform else "python  -m "

        self.write_restore_file(
            "update_q2rad",
            ("" if "win32" in sys.platform else "#!/bin/bash\n")
            + f"{pip_command} pip install --upgrade --force-reinstall q2gui"
            + f"&&{pip_command} pip install --upgrade --force-reinstall q2db"
            + f"&&{pip_command} pip install --upgrade --force-reinstall q2report"
            + f"&&{pip_command} pip install --upgrade --force-reinstall q2terminal"
            + f"&&{pip_command} pip install --upgrade --force-reinstall q2rad",
        )

    def get_github_package_release_version(self, git_package):
        response = read_url(f"{git_package}/releases/latest/download/version.py").decode("utf-8-sig").strip()
        release_path = ""
        if response:
            latest_version = re.findall(r"\d*\.\d*\.\d*", response)[0]
            release_path = read_url(f"{git_package}/releases/latest/download/latest")
            release_path = (
                f"{git_package}/releases/latest/download/{release_path.decode('utf-8-sig').strip()}"
            )
        else:
            latest_version = None
        return latest_version, release_path

    def get_package_versions(self, package, pipname=None):
        if not isinstance(package, str):
            pipname = package[1]
            package = package[0]
        if pipname is None:
            pipname = package
        installed_packages = [f"{d.metadata['Name']}" for d in distributions()]
        if package in installed_packages:
            try:
                current_version = version2(package)
            except Exception as error:
                _logger.error(f"Error checking version of {package}: {error}")
                current_version = None
            if current_version is None:
                try:
                    current_version = self.code_runner(
                        f"from {package} import __version__ as tmpv;return tmpv"
                    )()
                except Exception as error:
                    _logger.error(f"Error checking version of {package}: {error}")
            # if current_version is None:
            #     q2mess(f"Error checking curent version of {package}!")
        else:
            current_version = None

        # get latest version
        if re.findall(r"https://github.com/.*", pipname):  # git release
            latest_version, release_path = self.get_github_package_release_version(pipname)
            return latest_version, current_version
        else:
            response = open_url(
                f"https://pypi.python.org/pypi/{pipname if pipname else package}/json",
                timeout=1,
            )  # noqa F405
            if response:
                latest_version = json.load(response)["info"]["version"]
            else:
                latest_version = None

            return latest_version, current_version

    def get_git_package_version(git_package):
        package_name = os.path.basename(git_package)
        package_path = git_package.replace("github.com", "githubusercontent.com")
        version_url = f"https://raw.{package_path}/main/{package_name}/version.py"
        return read_url(version_url).decode().split("=")[-1].strip()

    def update_packages(self, packages_list=q2_modules, force=False):
        if self.frozen:
            return
        upgraded = []
        w = Q2WaitShow(len(packages_list))
        for package in packages_list:
            _package = package if isinstance(package, str) else package[0]
            if w.step(f"{_package}"):
                break
            latest_version, current_version = self.get_package_versions(package)
            if isinstance(package, (list, tuple)) and len(package) > 1:
                if re.findall(r"https://github.com/.*", package[1]):  # git release
                    _tmp, package = self.get_github_package_release_version(package[1])
            if self.db_logic is not None and package not in q2_modules:
                pkg_ver = get(
                    "packages",
                    f"package_name='{_package}'",
                    "package_version",
                    q2_db=self.db_logic,
                )
                if pkg_ver != "":
                    try:
                        latest_version = version.parse(pkg_ver)
                    except Exception as error:
                        q2mess(
                            f"Error parsing version for <b>{package}</b>:"
                            f"<br> {error}<br>"
                            f"<b>{package}</b> packages update interrupted"
                        )
                        continue
            self.process_events()
            if force or latest_version != current_version and latest_version:
                try:
                    self.pip_install(package, latest_version)
                except Exception as error:
                    try:
                        self.pip_install(package, latest_version)
                    except Exception as error:
                        latest_version = None
                        logging.warning(f"pip update {package} error:{error}")
                if latest_version:
                    upgraded.append(f"{_package} - <b>{current_version}</b> ⭆ <b>{latest_version}</b>")
                else:
                    upgraded.append(f"Error occured while updating package <b>{_package}</b>!")
        w.close()

        if upgraded:
            mess = ("Upgrading complete!<p>The program will be restarted!<p><p>") + "<p>".join(upgraded)
        else:
            mess = "Updates not found!<p>"
        q2mess(mess)
        if upgraded:
            self.restart()

    def update_from_git(self, package="", source="git"):
        if self.frozen:
            return
        if os.path.isfile("poetry.lock"):
            q2mess("poetry.lock presents - update from git is impossible!")
            return

        def callback(data):
            print(data)

        trm = Q2Terminal(callback=callback)
        executable = sys.executable.replace("w.exe", ".exe")
        w = Q2WaitShow(len(q2_modules))
        _source_suffix = ""
        _source_postfix = ""
        if source == "git":
            _source_suffix = "git+https://github.com/AndreiPuchko/"
            _source_postfix = ".git"
        for package in q2_modules:
            if w.step(package):
                break
            if not package.startswith("q2"):
                continue
            if package and package != package:
                continue
            trm.run(
                f"{executable} -m pip install  --upgrade --force-reinstall --no-deps"
                f" {_source_suffix}{package}{_source_postfix}"
            )
            if trm.exit_code != 0:
                q2mess(f"Error occured while updating <b>{package}</b>! See output for details.")
        w.close()
        q2Mess("Finished!<p>The program will be restarted!")
        self.restart()

    def restart(self):
        if "win32" in sys.platform:
            subprocess.Popen([sys.executable, "-m", "q2rad"], start_new_session=True)
        else:
            os.execv(sys.executable, [sys.executable, "-m", "q2rad"])
        self.close()

    def pip_install(self, package, latest_version=""):
        if self.frozen:
            return

        if isinstance(package, tuple) or isinstance(package, list):
            package = package[1] if package[1] else package[0]
        if re.findall(r"https://github.com/.*", package):
            if not package.endswith(".whl"):
                _tmp, package = self.get_github_package_release_version(package)
            latest_version = ""
        latest_version = f"=={latest_version}" if latest_version else ""

        def pip_runner(package):
            def worker():
                trm = Q2Terminal(callback=print)
                trm.run(
                    f'"{sys.executable.replace("w.exe", ".exe")}" -m pip install '
                    f"--upgrade --no-cache-dir {package}"
                    f"{latest_version}"
                )
                trm.close()

            return worker

        q2working(pip_runner(package), _("Installing package %s...") % package)

    def pip_uninstall(self, package):
        if self.frozen:
            return

        def pip_runner():
            trm = Q2Terminal(callback=print)
            trm.run(f'"{sys.executable.replace("w.exe", ".exe")}" -m pip uninstall -y {package}')
            trm.close()

        q2working(pip_runner, _("Uninstalling package %s...") % package)

    def check_app_update(self, force_update=False):
        # self.update_app_packages()
        # if self.frozen:
        #     return

        if not os.path.isdir(self.q2market_path) and self.app_url or force_update:
            try:
                market_version = read_url(self.app_url + ".version").decode("utf-8")  # noqa F405
            except Exception as e:  # noqa F841
                self.show_statusbar_mess("An error occurred while checking for updates")
                return
            if force_update or (market_version and market_version > self.app_version):
                if force_update:
                    update_detected = f"You are about to rewrite current App <b>{self.app_title}</b>!"
                else:
                    update_detected = f"Update for App <b>{self.app_title}</b> detected!"
                if (
                    q2AskYN(
                        f"{update_detected}"
                        f"<p>Current version <b>{self.app_version}</b>"
                        f"<p>New version <b>{market_version}</b>"
                        "<p>Download and install?"
                    )
                    == 2
                ):
                    data = json.load(open_url(self.app_url + ".json"))  # noqa F405
                    AppManager.import_json_app(data)
                    # self.open_selected_app()
                    return True

    def check_ext_update(self, prefix="", force_update=False, _ext_url=""):
        # if self.frozen:
        #     return
        if prefix:
            cu = q2cursor(f"select * from extensions where prefix='{prefix}'")
        else:
            cu = q2cursor(f"select * from extensions where checkupdates<>'' order by seq")
        updated = None
        for row in cu.records():
            _prefix = row["prefix"]

            if _ext_url:
                ext_url = f"{_ext_url}/{_prefix}"
            elif self.app_url:
                ext_url = f"{os.path.dirname(self.app_url)}/{_prefix}"
            else:
                ext_url = f"{self.q2market_url}/{_prefix}"

            ext_version = row["version"]
            if not os.path.isdir(self.q2market_path) or force_update:
                try:
                    market_version = read_url(ext_url + ".version").decode("utf-8")  # noqa F405
                except Exception as e:  # noqa F841
                    self.show_statusbar_mess("An error occurred while checking for updates")
                    continue
                if force_update or (market_version and market_version > ext_version):
                    if force_update:
                        update_detected = (
                            f"You are about to rewrite current Extension ({_prefix}) <b>{self.app_title}</b>!"
                        )
                    else:
                        update_detected = (
                            f"Update for Extension ({_prefix}) <b>{self.app_title}</b> detected!"
                        )
                    if (
                        q2AskYN(
                            f"{update_detected}"
                            f"<p>Current version <b>{ext_version}</b>"
                            f"<p>New version <b>{market_version}</b>"
                            "<p>Download and install?"
                        )
                        == 2
                    ):
                        data = json.load(open_url(ext_url + ".json"))  # noqa F405
                        AppManager.import_json_app(data, prefix=_prefix)
                        update("extensions", {"prefix": row["prefix"], "version": market_version})
                        updated = True
        # self.open_selected_app()
        return updated

    def update_app_packages(self):
        if self.frozen:
            return
        extra_packages = [
            (x["package_name"], x["package_pipname"])
            for x in q2cursor("select * from packages", self.db_logic).records()
        ]
        self.check_packages_update(extra_packages)

    def check_packages_update(self, packages_list=q2_modules):
        if self.frozen:
            return
        if len(packages_list) == 0:
            return
        can_upgrade = False
        if packages_list == q2_modules:
            packages_list.insert(0, "pip")
        list_2_upgrade_message = []
        list_2_upgrade = []

        rez = self.get_packages_version(packages_list)
        for package in rez:
            latest_version, current_version = rez[package]
            if self.db_logic is not None and package not in q2_modules:
                pkg_ver = get(
                    "packages",
                    f"package_name='{package if isinstance(package, str) else package[0]}'",
                    "package_version",
                    q2_db=self.db_logic,
                )
                pkg_ver = pkg_ver if pkg_ver else "99999"
                if pkg_ver != "":
                    try:
                        if current_version is None:
                            pass
                        elif version.parse(current_version) < version.parse(pkg_ver):
                            pass
                        elif version.parse(latest_version) > version.parse(pkg_ver):
                            continue
                    except Exception as error:
                        q2mess(
                            f"Error parsing version for <b>{package}</b>:"
                            f"<br> {error}<br>"
                            f"<b>{package}</b> packages update skipped"
                        )
                        continue
            if latest_version != current_version and latest_version:
                list_2_upgrade_message.append(
                    f"<b>{package if isinstance(package, str) else package[0]}</b>: "
                    f"{current_version} > {latest_version}"
                )
                list_2_upgrade.append(package)
                if not can_upgrade:
                    can_upgrade = True
        if can_upgrade:
            if (
                q2AskYN(
                    "Updates for packages are avaiable!<p><p>"
                    f"{',<br> '.join(list_2_upgrade_message)}<br><br>"
                    "Do you want to proceed with update?<p><p>"
                    "The program will be restarted after the update!"
                )
                == 2
            ):
                self.update_packages(list_2_upgrade)

    def get_packages_version(self, packages_list):
        task = Q2Tasker("Checking packages version")
        for package in packages_list:
            task.add(self.get_package_versions, package, name=package)
        rez = task.wait()
        return rez

    def run_stylesettings(self):
        AppStyleSettings().run()

    def run_constants(self):
        Q2Constants().run()

    def run_app_manager(self):
        AppManager().run()

    def create_form_menu(self):
        cu = q2cursor(
            """select
                menu_path
                , title
                , toolbar
                , menu_text
                , menu_before
                , menu_icon
                , menu_tiptext
                , menu_separator
                , name
            from forms
            where menu_path <> ''
            order by seq
            """,
            self.db_logic,
        )
        for x in cu.records():
            if x["menu_separator"]:
                self.add_menu(x["menu_path"] + "|-")

            menu_path = x["menu_path"] + "|" + (x["menu_text"] if x["menu_text"] else x["title"])

            def menu_worker(name):
                def real_worker():
                    self.run_form(name)

                return real_worker

            self.add_menu(
                menu_path,
                # worker=menu_worker(x["name"]),
                worker=partial(self.run_form, x["name"]),
                toolbar=x["toolbar"],
                before=x["menu_before"],
                icon=x["menu_icon"],
            )

    def run_forms(self):
        Q2Forms().run()

    def run_modules(self):
        Q2Modules().run()

    def run_queries(self):
        Q2Queries().run()

    def run_reports(self):
        Q2Reports().run()

    def run_packages(self):
        Q2Packages().run()

    def run_extensions(self):
        Q2Extensions().run()

    def run_finder(self):
        class Q2Finder:
            def __init__(self, find_string):
                self.find_string = find_string

            def get_columns_sql(self, table):
                return "select {{}} from `{}` where concat({}) like".format(
                    table,
                    ", ".join([f"`{x}`" for x in q2app.q2_app.db_logic.get_database_columns(table).keys()]),
                )

            def show_lines(self, table="lines"):
                sql = self.get_columns_sql(table).format("id") + " '%{}%'".format(self.find_string)
                where = "id in ({})".format(
                    ", ".join([x["id"] for x in q2cursor(sql, q2app.q2_app.db_logic).records()])
                )
                {"actions": Q2Actions, "lines": Q2Lines}[table]().run(where=where)

            def show_other(self, table):
                sql = self.get_columns_sql(table).format("name") + " '%{}%'".format(self.find_string)
                where = "name in ({})".format(
                    ", ".join(['"' + x["name"] + '"' for x in q2cursor(sql, q2app.q2_app.db_logic).records()])
                )
                {"forms": Q2Forms, "reports": Q2Reports, "modules": Q2Modules, "queries": Q2Queries}[
                    table
                ]().run(where=where)

        finder = Q2Form("Finder")

        finder.add_control("find_string", "Find string", datalen=150)
        finder.add_control("/")
        finder.add_control("/h", "in")
        finder.add_control(
            "button",
            "Forms",
            control="button",
            valid=lambda: Q2Finder(finder.s.find_string).show_other("forms"),
        )
        finder.add_control(
            "button",
            "Lines",
            control="button",
            valid=lambda: Q2Finder(finder.s.find_string).show_lines("lines"),
        )
        finder.add_control(
            "button",
            "Actions",
            control="button",
            valid=lambda: Q2Finder(finder.s.find_string).show_lines("actions"),
        )
        finder.add_control(
            "button",
            "Modules",
            control="button",
            valid=lambda: Q2Finder(finder.s.find_string).show_other("modules"),
        )
        finder.add_control(
            "button",
            "Queries",
            control="button",
            valid=lambda: Q2Finder(finder.s.find_string).show_other("queries"),
        )
        finder.add_control(
            "button",
            "Reports",
            control="button",
            valid=lambda: Q2Finder(finder.s.find_string).show_other("reports"),
        )
        finder.cancel_button = 1
        finder.run()

    def read_the_docs(self):
        webbrowser.open_new_tab("https://github.com/AndreiPuchko/q2rad/blob/main/docs/index.md")

    def make_binary(self):
        make_binary(self)

    def run_form(self, name, order="", where=""):
        form = self.get_form(name, where=where, order=order)
        form.run()

    def get_form(
        self,
        name,
        order="",
        where="",
    ):
        if not name:
            return
        form_dic = self.db_logic.get("forms", f"name ='{name}'")

        if form_dic == {}:
            return None

        sql = f"""
            select
                `column`
                , label
                , gridlabel
                , tag
                , mess
                , alignment
                , nogrid
                , noform
                , `check`
                , control
                , stretch
                , pic
                , datatype
                , datalen
                , datadec
                , migrate
                , disabled
                , readonly
                , pk
                , ai
                , to_table
                , to_column
                , related
                , to_form
                , code_valid as valid
                , code_when as _when
                , code_show as _show
                , style
            from `lines`
            where name = '{name}'
            order by seq
            """
        cu: Q2Cursor = q2cursor(sql, self.db_logic)

        mem = form = Q2Form(form_dic["title"])
        form._name = name
        form.no_view_action = False if form_dic["view_action"] else True
        form.ok_button = form_dic["ok_button"]
        form.cancel_button = form_dic["cancel_button"]

        form.valid = self.code_runner(form_dic["form_valid"], form)
        form.form_refresh = self.code_runner(form_dic["form_refresh"], form)

        form.after_form_closed = self.code_runner(form_dic["after_form_closed"], form)

        form.before_form_build = self.code_runner(form_dic["before_form_build"], form)
        form.before_grid_build = self.code_runner(form_dic["before_grid_build"], form)

        form.before_form_show = self.code_runner(form_dic["before_form_show"], form)
        form.after_form_show = self.code_runner(form_dic["after_form_show"], form)

        form.before_grid_show = self.code_runner(form_dic["before_grid_show"], form)
        form.after_grid_show = self.code_runner(form_dic["after_grid_show"], form)

        form.before_crud_save = self.code_runner(form_dic["before_crud_save"], form)
        form.after_crud_save = self.code_runner(form_dic["after_crud_save"], form)

        form.before_delete = self.code_runner(form_dic["before_delete"], form)
        form.after_delete = self.code_runner(form_dic["after_delete"], form)

        # add controls
        for control in cu.records():
            control["valid"] = self.code_runner(control["valid"], form)
            if control.get("_show"):
                control["show"] = self.code_runner(control["_show"], form)
            control["when"] = self.code_runner(control["_when"], form)
            form.add_control(**control)
            run_module("_e_control", _locals=locals())

        # add datasource
        if form_dic["form_table"]:
            form_cursor: Q2Cursor = self.db_data.table(
                table_name=form_dic["form_table"],
                order=order if order else form_dic["form_table_sort"],
                where=where,
            )
            form_model = Q2CursorModel(form_cursor)
            form.set_model(form_model)
        # add actions

        ext_actions = []
        for row in q2cursor("select prefix from extensions order by seq").records():
            ext_name = row["prefix"]
            if (
                get("actions", f"name='{ext_name}{name}'", "name", q2app.q2_app.db_logic)
                == f"{ext_name}{name}"
            ):
                ext_actions.append(
                    f"""select * from (select * from actions 
                                        where name = '{ext_name}{name}' order by seq) qq"""
                )
        ext_actions.append(
            f"""select * from (select * from actions 
                                        where name = '_{name}' order by seq) qq"""
        )
        if ext_actions:
            ext_select = " union all  " + " union all  ".join(ext_actions)
        else:
            ext_select = ""
        sql = f"select * from (select * from actions where name = '{name}' order by seq ) qq {ext_select}"
        cu = q2cursor(sql, self.db_logic)
        for action in cu.records():
            if action["action_mode"] == "1":
                form.add_action("/crud")
            elif action["action_mode"] == "3":
                form.add_action("-")
            else:
                if action["child_form"] and action["child_where"]:
                    child_form_name = action["child_form"]

                    def get_action_form(child_form_name):
                        def worker():
                            return self.get_form(child_form_name)

                        return worker

                    form.add_action(
                        action["action_text"],
                        self.code_runner(action["action_worker"]) if action["action_worker"] else None,
                        child_form=get_action_form(child_form_name),
                        child_where=action["child_where"],
                        hotkey=action["action_key"],
                        mess=action["action_mess"],
                        icon=action["action_icon"],
                        tag=action["tag"],
                        child_noshow=action["child_noshow"],
                        child_copy_mode=action["child_copy_mode"],
                        eof_disabled=1,
                    )
                else:
                    form.add_action(
                        action["action_text"],
                        (
                            self.code_runner(action["action_worker"], form=form)
                            if action["action_worker"]
                            else None
                        ),
                        hotkey=action["action_key"],
                        icon=action["action_icon"],
                        mess=action["action_mess"],
                        tag=action["tag"],
                        child_noshow=action["child_noshow"],
                        child_copy_mode=action["child_copy_mode"],
                        eof_disabled=action["eof_disabled"],
                    )
            run_module("_e_action", _locals=locals())
        self.code_runner(form_dic["after_form_load"], form)()
        return form

    def code_compiler(self, script: str):
        """
        Compile & preprocess script:
        - ?expr  -> print(expr)
        - top-level return -> RETURN = expr; raise ReturnEvent()
        - import <name> for internal modules -> runtime code that runs run_module(...),
        creates types.ModuleType(name), fills it and registers in sys.modules, then binds name.
        - from <name> import ... for internal modules -> same: ensure sys.modules[name] exists, then keep original ImportFrom.
        Returns {"code": codeobj or False, "error": msg, "script": processed_script}
        """
        import ast
        import traceback

        # helper: check DB for internal module
        def is_internal_module(name: str) -> bool:
            # only check top-level module name (before dot)
            base = name.split(".")[0]
            try:
                return bool(self.db_logic.get("modules", f"name='{base}'", "name"))
            except Exception:
                return False

        # Step 1: quick pre-pass to convert leading ?expr -> __q2print__(expr)
        # We only convert when ? is the first non-space character on the line.
        lines = []
        for raw in script.splitlines():
            stripped = raw.lstrip()
            if stripped.startswith("?"):
                indent = raw[: len(raw) - len(stripped)]
                expr = stripped[1:].lstrip()
                # wrap into a recognizable call; AST transformer will replace it with print(...)
                lines.append(f"{indent}__q2print__({expr})")
            else:
                lines.append(raw)
        preprocessed = "\n".join(lines)

        # Step 2: AST transformer
        class Transformer(ast.NodeTransformer):
            def __init__(self):
                super().__init__()
                self.def_level = 0  # >0 when inside function/class

            # track functions/classes depth
            def visit_FunctionDef(self, node):
                self.def_level += 1
                self.generic_visit(node)
                self.def_level -= 1
                return node

            def visit_AsyncFunctionDef(self, node):
                self.def_level += 1
                self.generic_visit(node)
                self.def_level -= 1
                return node

            def visit_ClassDef(self, node):
                self.def_level += 1
                self.generic_visit(node)
                self.def_level -= 1
                return node

            # replace top-level Return nodes with [Assign(RETURN=...), Raise(ReturnEvent())]
            def visit_Return(self, node: ast.Return):
                if self.def_level > 0:
                    return node  # inside def/class -> keep return
                # top-level return -> produce two statements
                value_node = node.value if node.value is not None else ast.Constant(value=None)
                assign = ast.Assign(targets=[ast.Name(id="RETURN", ctx=ast.Store())], value=value_node)
                raise_exc = ast.Raise(
                    exc=ast.Call(
                        func=ast.Name(id="ReturnEvent", ctx=ast.Load()),
                        args=[],
                        keywords=[],
                    ),
                    cause=None,
                )
                # return a list of nodes — NodeTransformer will splice them in place
                return [assign, raise_exc]

            # replace our marker call __q2print__(...) to actual print(...)
            def visit_Expr(self, node: ast.Expr):
                # detect Call to Name '__q2print__'
                if (
                    isinstance(node.value, ast.Call)
                    and isinstance(node.value.func, ast.Name)
                    and node.value.func.id == "__q2print__"
                ):
                    # reconstruct print(...) call
                    newcall = ast.Call(
                        func=ast.Name(id="print", ctx=ast.Load()),
                        args=node.value.args,
                        keywords=[],
                    )
                    return ast.Expr(value=newcall)
                return self.generic_visit(node)

            # handle import statements
            def visit_Import(self, node: ast.Import):
                # For each alias: if internal module -> replace import with code that:
                #  _mod_ns = run_module('modname', import_only=True)
                #  if isinstance(_mod_ns, dict):
                #      import types, sys
                #      _mod = types.ModuleType('modname')
                #      for k,v in _mod_ns.items(): setattr(_mod, k, v)
                #      sys.modules['modname'] = _mod
                #      globals()['<bindname>'] = _mod
                # else: keep original import (standard module)
                new_nodes = []
                for alias in node.names:
                    modname = alias.name  # e.g. 'time' or 'w1'
                    asname = alias.asname or modname.split(".")[0]

                    if is_internal_module(modname):
                        # _mod_ns = run_module('modname', import_only=True)
                        assign_ns = ast.Assign(
                            targets=[ast.Name(id="_mod_ns", ctx=ast.Store())],
                            value=ast.Call(
                                func=ast.Name(id="run_module", ctx=ast.Load()),
                                args=[ast.Constant(value=modname)],
                                keywords=[
                                    ast.keyword(
                                        arg="import_only",
                                        value=ast.Constant(value=True),
                                    )
                                ],
                            ),
                        )
                        new_nodes.append(assign_ns)

                        # if isinstance(_mod_ns, dict):
                        #   import types, sys
                        #   _mod = types.ModuleType('modname')
                        #   for k,v in _mod_ns.items(): setattr(_mod, k, v)
                        #   sys.modules['modname'] = _mod
                        #   globals()['asname'] = _mod
                        isinstance_check = ast.If(
                            test=ast.Call(
                                func=ast.Name(id="isinstance", ctx=ast.Load()),
                                args=[
                                    ast.Name(id="_mod_ns", ctx=ast.Load()),
                                    ast.Name(id="dict", ctx=ast.Load()),
                                ],
                                keywords=[],
                            ),
                            body=[
                                # import types, sys
                                ast.Import(
                                    names=[
                                        ast.alias(name="types", asname=None),
                                        ast.alias(name="sys", asname=None),
                                    ]
                                ),
                                # _mod = types.ModuleType('modname')
                                ast.Assign(
                                    targets=[ast.Name(id="_mod", ctx=ast.Store())],
                                    value=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id="types", ctx=ast.Load()),
                                            attr="ModuleType",
                                            ctx=ast.Load(),
                                        ),
                                        args=[ast.Constant(value=modname)],
                                        keywords=[],
                                    ),
                                ),
                                # for k,v in _mod_ns.items(): setattr(_mod,k,v)
                                ast.For(
                                    target=ast.Tuple(
                                        elts=[
                                            ast.Name(id="k", ctx=ast.Store()),
                                            ast.Name(id="v", ctx=ast.Store()),
                                        ],
                                        ctx=ast.Store(),
                                    ),
                                    iter=ast.Call(
                                        func=ast.Attribute(
                                            value=ast.Name(id="_mod_ns", ctx=ast.Load()),
                                            attr="items",
                                            ctx=ast.Load(),
                                        ),
                                        args=[],
                                        keywords=[],
                                    ),
                                    body=[
                                        ast.Expr(
                                            value=ast.Call(
                                                func=ast.Name(id="setattr", ctx=ast.Load()),
                                                args=[
                                                    ast.Name(id="_mod", ctx=ast.Load()),
                                                    ast.Name(id="k", ctx=ast.Load()),
                                                    ast.Name(id="v", ctx=ast.Load()),
                                                ],
                                                keywords=[],
                                            )
                                        )
                                    ],
                                    orelse=[],
                                ),
                                # sys.modules['modname'] = _mod
                                ast.Assign(
                                    targets=[
                                        ast.Subscript(
                                            value=ast.Attribute(
                                                value=ast.Name(id="sys", ctx=ast.Load()),
                                                attr="modules",
                                                ctx=ast.Load(),
                                            ),
                                            slice=ast.Index(value=ast.Constant(value=modname)),
                                            ctx=ast.Store(),
                                        )
                                    ],
                                    value=ast.Name(id="_mod", ctx=ast.Load()),
                                ),
                                # globals()['asname'] = _mod
                                ast.Assign(
                                    targets=[
                                        ast.Subscript(
                                            value=ast.Call(
                                                func=ast.Name(id="globals", ctx=ast.Load()),
                                                args=[],
                                                keywords=[],
                                            ),
                                            slice=ast.Index(value=ast.Constant(value=asname)),
                                            ctx=ast.Store(),
                                        )
                                    ],
                                    value=ast.Name(id="_mod", ctx=ast.Load()),
                                ),
                            ],
                            orelse=[],
                        )
                        new_nodes.append(isinstance_check)
                        # cleanup: del _mod_ns, _mod (optional) -- we can omit to keep traceability
                    else:
                        # keep original import for standard module
                        new_nodes.append(ast.Import(names=[ast.alias(name=modname, asname=alias.asname)]))
                return new_nodes

            # handle from ... import ...
            def visit_ImportFrom(self, node: ast.ImportFrom):
                # if node.module is internal -> insert run_module(...) before the ImportFrom,
                # then keep the original ImportFrom (Python will import from sys.modules[...] we created)
                mod = node.module
                if mod and is_internal_module(mod):
                    prep = ast.Assign(
                        targets=[ast.Name(id="_mod_ns", ctx=ast.Store())],
                        value=ast.Call(
                            func=ast.Name(id="run_module", ctx=ast.Load()),
                            args=[ast.Constant(value=mod)],
                            keywords=[ast.keyword(arg="import_only", value=ast.Constant(value=True))],
                        ),
                    )
                    # create module object if _mod_ns is dict (same as above)
                    setup = ast.If(
                        test=ast.Call(
                            func=ast.Name(id="isinstance", ctx=ast.Load()),
                            args=[
                                ast.Name(id="_mod_ns", ctx=ast.Load()),
                                ast.Name(id="dict", ctx=ast.Load()),
                            ],
                            keywords=[],
                        ),
                        body=[
                            ast.Import(
                                names=[
                                    ast.alias(name="types", asname=None),
                                    ast.alias(name="sys", asname=None),
                                ]
                            ),
                            ast.Assign(
                                targets=[ast.Name(id="_mod", ctx=ast.Store())],
                                value=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id="types", ctx=ast.Load()),
                                        attr="ModuleType",
                                        ctx=ast.Load(),
                                    ),
                                    args=[ast.Constant(value=mod)],
                                    keywords=[],
                                ),
                            ),
                            ast.For(
                                target=ast.Tuple(
                                    elts=[
                                        ast.Name(id="k", ctx=ast.Store()),
                                        ast.Name(id="v", ctx=ast.Store()),
                                    ],
                                    ctx=ast.Store(),
                                ),
                                iter=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id="_mod_ns", ctx=ast.Load()),
                                        attr="items",
                                        ctx=ast.Load(),
                                    ),
                                    args=[],
                                    keywords=[],
                                ),
                                body=[
                                    ast.Expr(
                                        value=ast.Call(
                                            func=ast.Name(id="setattr", ctx=ast.Load()),
                                            args=[
                                                ast.Name(id="_mod", ctx=ast.Load()),
                                                ast.Name(id="k", ctx=ast.Load()),
                                                ast.Name(id="v", ctx=ast.Load()),
                                            ],
                                            keywords=[],
                                        )
                                    )
                                ],
                                orelse=[],
                            ),
                            ast.Assign(
                                targets=[
                                    ast.Subscript(
                                        value=ast.Attribute(
                                            value=ast.Name(id="sys", ctx=ast.Load()),
                                            attr="modules",
                                            ctx=ast.Load(),
                                        ),
                                        slice=ast.Index(value=ast.Constant(value=mod)),
                                        ctx=ast.Store(),
                                    )
                                ],
                                value=ast.Name(id="_mod", ctx=ast.Load()),
                            ),
                        ],
                        orelse=[],
                    )
                    return [prep, setup, node]
                return node

        # Step 3: parse AST, transform, compile
        try:
            tree = ast.parse(preprocessed)
            trans = Transformer()
            tree = trans.visit(tree)
            ast.fix_missing_locations(tree)
            codeobj = compile(tree, "<db_script>", "exec")
            return {"code": codeobj, "error": "", "script": preprocessed}
        except Exception as e:
            tb = traceback.format_exc()
            err = f"Code compile error: {e}\n{tb}"
            try:
                self._logger.error(err)
            except Exception:
                pass
            return {"code": False, "error": err, "script": preprocessed}

    def code_runner(self, script, form=None, __name__="__main__"):
        _form = form

        # to provide return ability for exec
        def real_runner(**args):
            __locals_dict = {
                "RETURN": None,
                "ReturnEvent": ReturnEvent,
                "num": num,
                "_logger": _logger,
                "mem": _form,
                "form": _form,
                "self": self,
                "q2_app": self,
                "myapp": self,
                "__name__": __name__,
            }
            for x in args:
                __locals_dict[x] = args[x]
            globals()["q2_app"] = self
            return run_module(script=script, _locals=__locals_dict)

        return real_runner

    def run_module(self, name=""):
        return run_module(name)

    def close(self):
        self.stop_local_mysql()
        return super().close()


def main():
    app = Q2RadApp("q2RAD")
    # app.dev_mode = 1
    app.run()


if __name__ == "__main__":
    main()
