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

if __name__ == "__main__":

    sys.path.insert(0, ".")


from q2rad import Q2App, Q2Form
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
from q2rad.q2actions import Q2Actions
from q2db.cursor import Q2Cursor
from q2rad.q2raddb import *  # noqa:F403

from q2gui import q2app
from q2rad.q2raddb import q2cursor
from q2rad.q2appmanager import AppManager
from q2rad.q2stylesettings import AppStyleSettings
from q2rad.q2utils import set_logging
from q2terminal.q2terminal import Q2Terminal
from q2rad.q2appselector import Q2AppSelect
from q2rad.q2modules import Q2Modules
from q2rad.q2forms import Q2Forms
from q2rad.q2lines import Q2Lines
from q2rad.q2market import Q2Market
from q2rad.q2packages import Q2Packages
from q2rad.q2constants import Q2Constants, q2const
from q2rad.q2queries import Q2Queries
from q2rad.q2reports import Q2Reports, Q2RadReport
from q2rad.q2utils import Q2Tasker
from q2rad.q2utils import auto_filter

import gettext

import json
import subprocess
import shutil
import pkgutil
import logging
import traceback


# TODO: excel custom format 2 report


q2_modules = ["q2rad", "q2gui", "q2db", "q2report", "q2terminal"]
const = q2const()
_ = gettext.gettext


set_logging()
_logger = logging.getLogger(__name__)


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


def run_module(module_name=None, globals=globals(), locals=locals(), script="", import_only=False):
    if module_name is not None:
        script = q2app.q2_app.db_logic.get("modules", f"name = '{module_name}'", "script")
    if not script:
        return
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

        class ReturnEvent(Exception):
            pass

        locals.update(
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
            exec(code["code"], globals, locals)
        except ReturnEvent:
            pass
        except Exception:
            explain_error()
        return locals["RETURN"]


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
            script[line_no - 1] = f"{err_char*10}\n{err_char*2}" + script[line_no - 1] + f"\n{err_char*10}"
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
        value = str(error["locals"][x])[:100]
        msg.append(f"{x}:{value}")
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

        _logger.warning("About to start")
        super().__init__(title)
        self.settings_title = "q2RAD"
        self.style_file = "q2rad.qss"
        self.db = None

        self.db_data = None
        self.db_logic = None
        self.last_root_password = ""
        self.selected_application = {}
        self.q2style.font_size = int_(self.settings.get("Style Settings", "font_size", "10"))  # noqa F405
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
        self.open_application(autoload_enabled=True)

    def open_application(self, autoload_enabled=False):
        Q2AppSelect().run(autoload_enabled)
        if self.selected_application != {}:
            self.open_selected_app(True)
            self.check_app_update()
            # self.update_app_packages()
        else:
            self.close()

    def open_selected_app(self, go_to_q2market=False):
        wait = Q2WaitShow(5, "Loading app> ")
        wait.step("Prepare")
        self.clear_app_info()
        wait.step("Migrate logic DB")
        self.migrate_db_logic()
        wait.step("Migrate data DB")
        self.migrate_db_data()
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

        if go_to_q2market and (
            max(
                [
                    self.db_logic.table("forms").row_count(),
                    self.db_logic.table("lines").row_count(),
                    self.db_logic.table("actions").row_count(),
                    self.db_logic.table("reports").row_count(),
                    self.db_logic.table("modules").row_count(),
                    self.db_logic.table("queries").row_count(),
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
        for form in (Q2Constants(),):
            for x in form.get_table_schema():
                data_schema.add(**x)

        self.db_data.set_schema(data_schema)
        if self.db_data.migrate_error_list:
            q2Mess(self.db_data.migrate_error_list)
        self.create_menu()

    def migrate_db_logic(self):
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
        self.db_logic.set_schema(data_schema)

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
                except Exception:
                    return None

    def open_databases(self):
        self.db_data = self._open_database(
            database_name=self.selected_application.get("database_data", ""),
            db_engine_name=self.selected_application.get("driver_data", "").lower(),
            host=self.selected_application.get("host_data", ""),
            port=self.selected_application.get("port_data", ""),
            guest_mode=self.selected_application.get("guest_mode", ""),
            user="q2user",
            password="q2password",
        )
        if self.db_data:
            self.db_logic = self._open_database(
                database_name=self.selected_application.get("database_logic", ""),
                db_engine_name=self.selected_application.get("driver_logic", "").lower(),
                host=self.selected_application.get("host_logic", ""),
                port=self.selected_application.get("port_logic", ""),
                user="q2user",
                password="q2password",
            )
        self.last_root_password = ""
        if self.db_data is None or self.db_logic is None:
            self.selected_application = {}
            q2Mess(_("Can not open database"))
            self.open_application()

    def create_menu(self):
        self.clear_menu()
        self.add_menu("File|About", self.about, icon="info.png")
        self.add_menu("File|Manage", self.run_app_manager, icon="tools.png")
        self.add_menu("File|Settings", self.run_stylesettings)
        self.add_menu("File|Constants", self.run_constants)
        self.add_menu("File|-")
        self.add_menu("File|Open", self.open_application, icon="open.png")
        self.add_menu("File|-")
        self.add_menu("File|Close", self.close, toolbar=1, icon="exit.png")

        self.create_form_menu()

        self.dev_mode = (
            self.selected_application.get("dev_mode")
            or os.path.isdir(self.q2market_path)
            or os.path.isfile(".dev")
        )
        # self.dev_mode = False

        if self.dev_mode:
            self.add_menu("Dev|Forms", self.run_forms, toolbar=self.dev_mode)
            self.add_menu("Dev|Modules", self.run_modules, toolbar=self.dev_mode)
            self.add_menu("Dev|Querys", self.run_queries, toolbar=self.dev_mode)
            self.add_menu("Dev|Reports", self.run_reports, toolbar=self.dev_mode)
            self.add_menu("Dev|Packages", self.run_packages, toolbar=self.dev_mode)
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
        if text:
            about.append(text)
        about.append("<b>q2RAD</b>")
        about.append("Versions:")
        about.append(f"<b>Python</b>: {sys.version}<p>")

        rez = self.get_packages_verion(q2_modules)

        for package in rez:
            latest_version, current_version = rez[package]
            if latest_version:
                if current_version != latest_version:
                    latest_version_text = f"({latest_version })"
                else:
                    latest_version_text = ""
            else:
                latest_version_text = _(" (Can't load package info)")

            about.append(f"<b>{package}</b>: {current_version}{latest_version_text}")

        q2Mess("<br>".join(about))

    def asset_file_loader(self, name):
        asset_url = f"{self.assets_url}/{name}"
        try:
            asset_content = read_url(asset_url)  # noqa F405
            if not asset_content:
                return False
        except Exception:
            print(f"Error reading {asset_url}")
            return False

        try:
            open(f"assets/{name}", "wb").write(asset_content)
            return True
        except Exception:
            print(f"Error writing asset/{name}")
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

        # create update_q2rad.sh
        self.write_restore_file(
            "update_q2rad",
            ("" if "win32" in sys.platform else "#!/bin/bash\n")
            + ("q2rad\\scripts\\activate " if "win32" in sys.platform else "source q2rad/bin/activate")
            + "&& pip install --upgrade --force-reinstall q2gui"
            + "&& pip install --upgrade --force-reinstall q2db"
            + "&& pip install --upgrade --force-reinstall q2report"
            + "&& pip install --upgrade --force-reinstall q2terminal"
            + "&& pip install --upgrade --force-reinstall q2rad",
        )

        # create run_q2rad
        self.write_restore_file(
            "run_q2rad",
            ("" if "win32" in sys.platform else "#!/bin/bash\n")
            + (
                "start q2rad\\scripts\\pythonw.exe -m q2rad"
                if "win32" in sys.platform
                else "q2rad/bin/q2rad\n"
            ),
        )
        if "win32" in sys.platform:
            open("run_q2rad.vbs", "w").write(
                'WScript.CreateObject("WScript.Shell").Run '
                '"q2rad\\scripts\\pythonw.exe -m q2rad", 0, false'
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
        if sys.platform != "darwin":
            if q2AskYN("Should I make a desktop shortcut?") == 2:
                self.make_desktop_shortcut()
        self.process_events()

    def get_package_versions(self, package):
        response = open_url(f"https://pypi.python.org/pypi/{package}/json")  # noqa F405
        if response:
            latest_version = json.load(response)["info"]["version"]
        else:
            latest_version = None
        installed_packages = [x.name for x in pkgutil.iter_modules()]
        if package in installed_packages:
            current_version = self.code_runner(f"from {package} import __version__ as tmpv;return tmpv")()
        else:
            current_version = None

        return latest_version, current_version

    def update_packages(self, packages_list=q2_modules, force=False):
        upgraded = []
        w = Q2WaitShow(len(packages_list))
        for package in packages_list:
            if w.step(package):
                break
            latest_version, current_version = self.get_package_versions(package)
            self.process_events()
            if force or latest_version != current_version and latest_version:
                try:
                    self.pip_install(package, latest_version)
                except Exception:
                    try:
                        self.pip_install(package, latest_version)
                    except Exception:
                        pass

                latest_version, new_current_version = self.get_package_versions(package)
                if latest_version:
                    upgraded.append(f"{package} - " f"<b>{current_version}</b> => " f"<b>{latest_version}</b>")
                else:
                    upgraded.append(f"Error occured while updating package <b>{package}</b>!")
        w.close()
        if upgraded:
            mess = ("Upgrading complete!<p>" "The program will be restarted!" "<p><p>") + "<p>".join(upgraded)
        else:
            mess = "Updates not found!<p>"
        q2Mess(mess)
        if upgraded:
            self.restart()

    def update_from_git(self, package="", source="git"):
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
                q2mess(f"Error occured while updateing <b>{package}</b>! See output for details.")
        w.close()
        q2Mess("Finished!<p>The program will be restarted!")
        self.restart()

    def restart(self):
        if "win32" in sys.platform:
            subprocess.Popen([sys.executable, "-m", "q2rad"], start_new_session=True)
        else:
            os.execv(sys.executable, [sys.executable, "-m", "q2rad"])
        self.close()

    def pip_install(self, package, latest_version):
        q2working(
            lambda: subprocess.check_call(
                [
                    sys.executable.replace("w.exe", ".exe"),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "--no-cache-dir",
                    f"{package}=={latest_version}",
                ],
                shell=True if "win32" in sys.platform else False,
            ),
            _("Installing package %s...") % package,
        )

    def pip_uninstall(self, package):
        q2working(
            lambda: subprocess.check_call(
                [
                    sys.executable.replace("w.exe", ".exe"),
                    "-m",
                    "pip",
                    "uninstall",
                    "-y",
                    f"{package}",
                ],
                shell=True if "win32" in sys.platform else False,
            ),
            _("Uninstalling package %s...") % package,
        )

    def check_app_update(self, force_update=False):
        # self.update_app_packages()

        if not os.path.isdir(self.q2market_path) and self.app_url and self.app_version or force_update:
            try:
                market_version = read_url(self.app_url + ".version").decode("utf-8")  # noqa F405
            except Exception as e:  # noqa F841
                self.show_statusbar_mess("An error occurred while checking for updates")
                return
            if force_update or market_version and market_version != self.app_version:
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
                    self.open_selected_app()

    def update_app_packages(self):
        extra_packages = [
            x["package_name"] for x in q2cursor("select * from packages", self.db_logic).records()
        ]
        self.check_packages_update(extra_packages)

    def check_packages_update(self, packages_list=q2_modules):
        if len(packages_list) == 0:
            return
        can_upgrade = False
        if packages_list == q2_modules:
            packages_list.insert(0, "pip")
        list_2_upgrade_message = []
        list_2_upgrade = []

        rez = self.get_packages_verion(packages_list)

        for package in rez:
            latest_version, current_version = rez[package]
            if latest_version != current_version and latest_version:
                list_2_upgrade_message.append(f"<b>{package}</b>: {current_version} > {latest_version}")
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

    def get_packages_verion(self, packages_list):
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
            menu_path = x["menu_path"] + "|" + (x["menu_text"] if x["menu_text"] else x["title"])

            def menu_worker(name):
                def real_worker():
                    self.run_form(name)

                return real_worker

            self.add_menu(
                menu_path,
                worker=menu_worker(x["name"]),
                toolbar=x["toolbar"],
                before=x["menu_before"],
                icon=x["menu_icon"]
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

    def run_form(self, name, order="", where=""):
        form = q2working(lambda: self.get_form(name, where=where, order=order), "Loading form...")
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
                , nogrid
                , noform
                , `check`
                , control
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
            from `lines`
            where name = '{name}'
            order by seq
            """
        cu: Q2Cursor = q2cursor(sql, self.db_logic)

        form = Q2Form(form_dic["title"])
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
        for x in cu.records():
            if x.get("to_form"):
                x["to_form"] = self.get_form(x["to_form"])
            x["valid"] = self.code_runner(x["valid"], form)
            if x.get("_show"):
                x["show"] = self.code_runner(x["_show"], form)
            x["when"] = self.code_runner(x["_when"], form)
            form.add_control(**x)

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
        sql = f"select * from actions where name = '{name}' order by seq"
        cu = q2cursor(sql, self.db_logic)
        for x in cu.records():
            if x["action_mode"] == "1":
                form.add_action("/crud")
            elif x["action_mode"] == "3":
                form.add_action("-")
            else:
                if x["child_form"] and x["child_where"]:
                    child_form_name = x["child_form"]

                    def get_action_form(child_form_name):
                        def worker():
                            return self.get_form(child_form_name)

                        return worker

                    form.add_action(
                        x["action_text"],
                        self.code_runner(x["action_worker"]) if x["action_worker"] else None,
                        child_form=get_action_form(child_form_name),
                        child_where=x["child_where"],
                        hotkey=x["action_key"],
                        icon=x["action_icon"],
                        tag=x["tag"],
                        child_noshow=x["child_noshow"],
                        child_copy_mode=x["child_copy_mode"],
                        eof_disabled=1,
                    )
                else:
                    form.add_action(
                        x["action_text"],
                        self.code_runner(x["action_worker"], form=form) if x["action_worker"] else None,
                        hotkey=x["action_key"],
                        icon=x["action_icon"],
                        tag=x["tag"],
                        child_noshow=x["child_noshow"],
                        child_copy_mode=x["child_copy_mode"],
                        eof_disabled=x["eof_disabled"],
                    )

        return form

    def code_compiler(self, script):
        if "return" in script or "?" in script or "import" in script:
            # modify script for
            new_script_lines = []
            in_def = False
            for x in script.split("\n"):
                # when in_def is True  - do not modify return
                if re.findall(r"^def|^class", x):
                    in_def = True
                elif not re.findall(r"^\s+", x):
                    in_def = False
                # return
                if in_def is False and re.findall(r"^\s*return\W*.*|;\s*return\W*.*", x):
                    if x.strip() == "return":
                        x = x.replace("return", "raise ReturnEvent")
                    else:
                        x = x.replace("return", "RETURN = ") + "; raise ReturnEvent"
                # print
                if re.findall(r"^\s*\?\W*.*", x):
                    # lets print it
                    x = x.split("?")[0] + "print(" + "".join(x.split("?")[1:]) + ")"
                # import
                if re.findall(r"^\s*import\W*.*", x):
                    module = x.split("import")[1].strip()
                    if self.db_logic.get("modules", f"name='{module}'", "name"):
                        x = x.split("import")[0] + f"run_module('{module}', import_only=True)"

                new_script_lines.append(x)
            script = "\n".join(new_script_lines)
        try:
            code = compile(script, f"<{script}>", "exec")
            return {"code": code, "error": ""}
        except Exception:
            error = sys.exc_info()[1]
            msg = []
            msg.append("Compile error:")
            msg.append(error.msg)
            msg.append(f"Line:{error.lineno}:{error.text}")
            msg.append("Code:")
            msg.append("-" * 25)
            msg.append(error.filename[1:-1])
            msg.append("-" * 25)
            msg = "\n".join(msg)
            _logger.error(msg)
            return {
                "code": False,
                "error": msg,
            }

    def code_runner(self, script, form=None, __name__="__main__"):
        _form = form

        # to provide return ability for exec
        def real_runner(**args):
            # make exec stop on return
            class ReturnEvent(Exception):
                pass

            __locals_dict = {
                "RETURN": None,
                "ReturnEvent": ReturnEvent,
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
            return run_module(script=script, locals=__locals_dict)

        return real_runner

    def run_module(self, name=""):
        return run_module(name)


def main():
    app = Q2RadApp("q2RAD")
    # app.dev_mode = 1
    app.run()


if __name__ == "__main__":
    main()
