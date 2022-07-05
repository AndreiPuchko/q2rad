import sys

if __name__ == "__main__":

    sys.path.insert(0, ".")


from q2rad import Q2App, Q2Form
from q2gui.q2dialogs import q2Mess, q2AskYN, q2WaitShow
from q2gui.q2model import Q2CursorModel
from q2db.schema import Q2DbSchema
from q2db.db import Q2Db
from q2rad.q2actions import Q2Actions
from q2db.cursor import Q2Cursor
from q2rad.q2raddb import read_url, open_url

from q2gui import q2app
from q2rad.q2raddb import q2cursor
from q2rad.q2appmanager import AppManager

# from random import randint

from q2rad.q2appselector import Q2AppSelect
from q2rad.q2modules import Q2Modules
from q2rad.q2forms import Q2Forms
from q2rad.q2lines import Q2Lines
from q2rad.q2constants import Q2Constants, q2const
from q2rad.q2queries import Q2Queries
from q2rad.q2reports import Q2Reports, Q2RadReport

import traceback
import gettext

# import urllib.request
import os
import json
import subprocess


q2_modules = ("q2rad", "q2gui", "q2db", "q2report")
const = q2const()
_ = gettext.gettext


def get_report(report_name):
    content = q2app.q2_app.db_logic.get("reports", f"name='{report_name}'", "content")
    if content:
        return Q2RadReport(content)
    else:
        q2Mess(f"Report not fount: {report_name}")
        return None


def run_module(module_name):
    q2app.q2_app.run_module(module_name)


class Q2RadApp(Q2App):
    def __init__(self, title=""):
        super().__init__(title)
        self.db = None

        self.db_data = None
        self.db_logic = None
        self.dev_mode = False
        self.selected_application = {}

        qss_file = "q2gui.qss"
        if not os.path.isfile(qss_file):
            qss_url = (
                "https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/q2gui.qss"
            )
            open(qss_file, "w").write(read_url(qss_url).decode("utf-8"))

        if os.path.isfile(qss_file):
            self.style_file = qss_file
            self.set_style_sheet()

        self.set_icon("assets/q2rad.ico")

        self.const = const

    def make_desktop_shortcut(self):
        if "win" in sys.platform:
            subprocess.check_call(["cscript", "make_shortcut.vbs"], shell=True)
        else:
            basepath = os.path.abspath(".")
            desktop_entry = [
                "[Desktop Entry]\n"
                "Name=q2RAD\n"
                f"Exec={basepath}/q2rad/bin/q2rad\n"
                f"Path={basepath}\n"
                f"Icon={basepath}/assets/q2rad.ico\n"
                "Terminal=false\n"
                "Type=Application\n"
            ]

            desktop = os.path.join(os.path.join(os.path.expanduser("~")), "Desktop")
            open(f"{desktop}/q2rad.desktop", "w").writelines("\n".join(desktop_entry))

    def asset_file_loader(self, name):
        try:
            open(f"assets/{name}", "wb").write(
                read_url(f"https://andreipuchko.github.io/q2rad/assets/{name}")
            )
        except Exception:
            print(f"Error reading asset/{name}")

    def write_restore_file(self, name, content):
        if "win" in sys.platform:
            u_file = open(f"{name}.bat", "w")
        else:
            u_file = open(os.open(f"{name}.sh", os.O_CREAT | os.O_WRONLY, 0o777), "w")
        u_file.write(content)
        u_file.close()

    def load_assets(self, force_reload=False):
        if os.path.isfile("poetry.lock"):
            return
        if os.path.isdir("assets") and force_reload is False:
            return
        if not os.path.isdir("assets"):
            os.mkdir("assets")
        # first run
        # load icons
        for x in ("q2rad.ico",):
            self.asset_file_loader(x)

        # create update_q2rad.sh
        self.write_restore_file(
            "update_q2rad",
            ("" if "win" in sys.platform else "#!/bin/bash\n")
            + (
                "q2rad\\scripts\\activate "
                if "win" in sys.platform
                else "source q2rad/bin/activate\n"
            )
            + "&& pip install --upgrade q2gui"
            + "&& pip install --upgrade q2db"
            + "&& pip install --upgrade q2report"
            + "&& pip install --upgrade q2rad",
        )

        # create run_q2rad
        self.write_restore_file(
            "run_q2rad",
            ("" if "win" in sys.platform else "#!/bin/bash\n")
            + (
                "start q2rad\\scripts\\pythonw.exe -m q2rad"
                if "win" in sys.platform
                else "q2rad/bin/q2rad\n"
            ),
        )
        if "win" in sys.platform:
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

        if q2AskYN("Can I make desktop shortcut?") == 2:
            self.make_desktop_shortcut()

    def on_start(self):
        if not os.path.isfile("poetry.lock"):
            self.load_assets()
            self.check_upgrade()
        self.open_application(autoload_enabled=True)

    def open_application(self, autoload_enabled=False):
        Q2AppSelect().run(autoload_enabled)
        if self.selected_application != {}:
            self.open_selected_app()
        else:
            self.close()

    def open_selected_app(self):
        self.migrate_db_logic()
        self.migrate_db_data()
        self.run_module("autorun")
        # DEBUG
        # self.run_forms()
        # self.run_queries()
        # self.run_modules()
        # self.run_reports()
        # self.run_app_manager()
        pass

    def migrate_db_data(self):
        data_schema = Q2DbSchema()
        cu = q2cursor(
            """
                select
                    forms.form_table as `table`
                    , lines.column
                    , lines.datatype
                    , lines.datalen
                    , lines.datadec
                    , lines.to_table
                    , lines.to_column
                    , lines.related
                    , lines.ai
                    , lines.pk
                from lines, forms
                where forms.name = lines.name
                    and form_table <>'' and migrate <>''
                """,
            self.db_logic,
        )
        for column in cu.records():
            data_schema.add(**column)
        for form in (Q2Constants(),):
            for x in form.get_table_schema():
                data_schema.add(**x)

        self.db_data.set_schema(data_schema)
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
        ):
            for x in form.get_table_schema():
                data_schema.add(**x)
        self.db_logic.set_schema(data_schema)

    def open_databases(self):
        self.db_data = Q2Db(database_name=self.selected_application["database_data"])
        self.db_logic = Q2Db(database_name=self.selected_application["database_logic"])

    def create_menu(self):
        self.clear_menu()
        self.add_menu("File|About", self.about)
        self.add_menu("File|Manage", self.run_app_manager)
        self.add_menu("File|Constants", self.run_constants)
        self.add_menu("File|-")
        self.add_menu("File|Open", self.open_application)
        self.add_menu("File|-")
        self.add_menu("File|Close", self.close, toolbar=1)

        self.create_form_menu()

        if self.dev_mode:
            self.add_menu("Dev|Forms", self.run_forms, toolbar=self.dev_mode)
            self.add_menu("Dev|Modules", self.run_modules, toolbar=self.dev_mode)
            self.add_menu("Dev|Querys", self.run_queries, toolbar=self.dev_mode)
            self.add_menu("Dev|Reports", self.run_reports, toolbar=self.dev_mode)
        self.build_menu()

    def about(self, text=""):
        about = []
        if text:
            about.append(text)
        about.append("<b>q2RAD</b><br>")
        about.append("Versions:")
        about.append(f"<b>Python</b>: {sys.version}<br>")
        # about.append("")
        w = q2WaitShow(len(q2_modules))
        for package in q2_modules:
            w.step()
            latest_version, current_version = self.get_package_versions(package)
            about.append(
                f"<b>{package}</b>: {current_version}"
                f"{'(' + latest_version + ' avaiable)' if current_version!=latest_version else ''}"
            )
        w.close()
        q2Mess("<br>".join(about))

    def get_package_versions(self, package):
        latest_version = json.load(
            open_url(f"https://pypi.python.org/pypi/{package}/json")
        )["info"]["version"]
        current_version = sys.modules[package].__version__
        return latest_version, current_version

    def update_packages(self):
        upgraded = []
        w = q2WaitShow(len(q2_modules))
        for package in q2_modules:
            if w.step(package):
                break
            latest_version, current_version = self.get_package_versions(package)
            if latest_version != current_version:
                runpip = lambda: subprocess.check_call(  # noqa:E731
                    [
                        sys.executable.replace("w.exe", ".exe"),
                        "-m",
                        "pip",
                        "install",
                        "--upgrade",
                        "--no-cache-dir",
                        f"{package}=={latest_version}",
                    ],
                    shell=True if "win" in sys.platform else False
                )
                try:
                    runpip()
                except Exception:
                    try:
                        runpip()
                    except Exception:
                        pass

                latest_version, new_current_version = self.get_package_versions(package)
                upgraded.append(
                    f"{package} - "
                    f"<b>{current_version}</b> => "
                    f"<b>{latest_version}</b>"
                )
        w.close()
        if upgraded:
            mess = (
                "Upgrading complete!<br>" "The program will be restarted!" "<br><br>"
            ) + "<br>".join(upgraded)
        else:
            mess = "Updates not found!<br>"
        q2Mess(mess)
        if upgraded:
            os.execv(sys.executable, [sys.executable, "-m", "q2rad"])
            # if "win" in sys.platform:
            #     os.execv(sys.executable, [sys.executable, "-m", "q2rad"])
            # else:
            #     os.execv(sys.argv[0], sys.argv)
            # self.close()

    def check_upgrade(self):
        can_upgrade = False
        for package in q2_modules:
            latest_version, current_version = self.get_package_versions(package)
            can_upgrade = latest_version != current_version
            if can_upgrade:
                break
        if can_upgrade:
            if (
                q2AskYN(
                    "Updates is avaiable!<br><br>"
                    "Do you want to proceed with update?<br><br>"
                    "The program will be restarted after the update!"
                )
                == 2
            ):
                self.update_packages()

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
            menu_path = (
                x["menu_path"]
                + "|"
                + (x["menu_text"] if x["menu_text"] else x["title"])
            )

            def menu_worker(name):
                def real_worker():
                    self.run_form(name)

                return real_worker

            self.add_menu(
                menu_path,
                worker=menu_worker(x["name"]),
                toolbar=x["toolbar"],
                before=x["menu_before"],
            )

    def run_forms(self):
        Q2Forms().run()

    def run_modules(self):
        Q2Modules().run()

    def run_queries(self):
        Q2Queries().run()

    def run_reports(self):
        Q2Reports().run()

    def run_form(self, name):
        self.get_form(name).run()

    def get_form(self, name):
        if not name:
            return
        form_dic = self.db_logic.get("forms", f"name ='{name}'")

        sql = f"""
            select
                column
                ,label
                ,gridlabel
                ,nogrid
                ,noform
                ,`check`
                ,control
                ,pic
                ,datatype
                ,datalen
                ,datadec
                ,migrate
                ,pk
                ,ai
                ,to_table
                ,to_column
                ,related
                ,to_form
            from lines
            where name = '{name}'
            order by seq
            """
        cu = q2cursor(sql, self.db_logic)

        form = Q2Form(form_dic["title"])
        form.no_view_action = 1
        form.ok_button = form_dic["ok_button"]
        form.cancel_button = form_dic["cancel_button"]

        form.valid = self.code_runner(form_dic["form_valid"], form)

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
            form.add_control(**x)

        # add actions
        if form_dic["form_table"]:
            form_cursor: Q2Cursor = self.db_data.table(
                table_name=form_dic["form_table"]
            )
            form_model = Q2CursorModel(form_cursor)
            form.set_model(form_model)
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
                        form.add_action(
                            x["action_text"],
                            self.code_runner(x["action_worker"])
                            if x["action_worker"]
                            else None,
                            child_form=lambda: self.get_form(child_form_name),
                            child_where=x["child_where"],
                            hotkey=x["action_key"],
                        )
                    else:
                        form.add_action(
                            x["action_text"],
                            self.code_runner(x["action_worker"], form=form)
                            if x["action_worker"]
                            else None,
                            hotkey=x["action_key"],
                        )
        return form

    def code_error(self):
        return traceback.format_exc().replace("\n", "<br>").replace(" ", "&nbsp;")

    def code_compiler(self, script):
        script = script.replace("return", "pass;")
        try:
            code = compile(script, "'<worker>'", "exec")
            return {"code": code, "error": ""}
        except Exception:
            trace = self.code_error()
            return {
                "code": False,
                "error": f"""Compile error:<br><br>{trace}""",
            }

    def code_runner(self, script, form=None, __name__="__main__"):
        _form = form
        # to provide return ability for exec
        if "return " in script:
            nsl = []
            for x in script.split("\n"):
                if "return " in x:
                    if x.strip() == "return":
                        x = x.replace("return", "raise ReturnEvent")
                    else:
                        x = x.replace("return", "RETURN = ") + "; raise ReturnEvent"
                nsl.append(x)
            script = "\n".join(nsl)

        def real_runner():
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
                "__name__": __name__,
            }
            code = self.code_compiler(script)
            if code["code"]:
                try:
                    exec(code["code"], globals(), __locals_dict)
                except ReturnEvent:
                    pass
                except Exception:
                    trace = self.code_error()
                    q2Mess(f"""Runtime error:<br><br>{trace}""")
            else:
                q2Mess(code["error"])

            return __locals_dict["RETURN"]

        return real_runner

    def run_module(self, name=""):
        script = self.db_logic.get("modules", f"name = '{name}'", "script")
        if script:
            return self.code_runner(script)()


def main():
    # qss_file = "q2gui.qss"
    # if not os.path.isfile(qss_file):
    #     qss_url = "https://raw.githubusercontent.com/AndreiPuchko/q2rad/main/q2gui.qss"
    #     open(qss_file, "w").write(
    #         urllib.request.urlopen(qss_url).read().decode("utf-8")
    #     )
    app = Q2RadApp("q2RAD")
    app.dev_mode = 1
    app.run()


if __name__ == "__main__":
    main()
