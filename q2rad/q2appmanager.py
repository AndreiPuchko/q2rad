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


from q2db.db import Q2Db
from q2gui.q2utils import num
from q2gui import q2app
from q2gui.q2dialogs import q2AskYN, q2Mess, Q2WaitShow, q2ask, q2working

from q2rad import Q2Form
from q2terminal.q2terminal import Q2Terminal
from q2rad.q2raddb import insert, update, get
from datetime import datetime
from urllib.parse import urlparse
from q2rad.q2utils import ftp_upload

import json
import os

app_tables = [
    "forms",
    "lines",
    "actions",
    "reports",
    "modules",
    "queries",
    "packages",
]


class AppManager(Q2Form):
    def __init__(self, title=""):
        super().__init__("Manage q2Application")
        self.selected_tables = []

    def on_init(self):
        app_data = q2app.q2_app.selected_application
        frozen = q2app.q2_app.frozen
        # frozen = 1

        self.add_control("/")
        if not frozen:
            if self.add_control("/h", "Platform"):
                if not q2app.q2_app.frozen:
                    self.add_control(
                        "upgrade",
                        "Check updates",
                        control="button",
                        valid=q2app.q2_app.update_packages,
                    )

                    self.add_control("/s")

                    self.add_control(
                        "reinstall_",
                        "Reinstall",
                        control="button",
                        valid=self.reinstall,
                    )

                    self.add_control(
                        "reinstall_git",
                        "Reinstall from GitHub",
                        control="button",
                        valid=self.update_from_git,
                    )

                    self.add_control("/s")

                self.add_control(
                    "reload_assets",
                    "Reload assets",
                    control="button",
                    valid=self.reload_assets,
                )

                self.add_control("/")

        if self.add_control("/v", "Application"):
            if self.add_control("/f"):
                self.add_control(
                    "",
                    "App title",
                    control="line",
                    data=q2app.q2_app.app_title,
                    readonly=1,
                )
                if not frozen and q2app.q2_app.app_url:
                    self.add_control(
                        "",
                        "App URL",
                        control="line",
                        data=q2app.q2_app.app_url,
                        readonly=1,
                    )
                if q2app.q2_app.app_version:
                    self.add_control(
                        "",
                        "App version",
                        control="line",
                        data=q2app.q2_app.app_version,
                        readonly=1,
                    )
                self.add_control("/")

            if not frozen:
                if self.add_control("/h", "Database"):
                    self.add_control(
                        "drl",
                        "Type",
                        data=app_data["driver_logic"].lower(),
                        readonly=1,
                        datalen=len(app_data["driver_logic"].strip()) + 5,
                    )
                    self.add_control(
                        "dtl",
                        "Name",
                        data=app_data["database_logic"],
                        readonly=1,
                        datalen=len(app_data["database_logic"].strip()),
                    )
                    if app_data.get("host_logic"):
                        self.add_control(
                            "hl",
                            "Host",
                            data=app_data["host_logic"],
                            readonly=1,
                            datalen=len(app_data["host_logic"].strip()),
                        )
                    if num(app_data.get("port_logic")):
                        self.add_control(
                            "pl",
                            "Port",
                            data=app_data["port_logic"],
                            readonly=1,
                            datalen=len(f"{app_data['port_logic']}") + 5,
                        )
                    self.add_control("/s")
                    self.add_control("/")

                if self.add_control("/h", ""):
                    self.add_control(
                        "exts",
                        "Extensions",
                        control="button",
                        # datalen=13,
                        valid=q2app.q2_app.run_extensions,
                    )

                    self.add_control("/s")
                    if self.add_control("/h", "Export"):
                        self.add_control(
                            "save_app",
                            "As JSON file",
                            control="button",
                            # datalen=13,
                            valid=self.export_app,
                        )
                        if os.path.isdir(self.q2_app.q2market_path):
                            self.add_control(
                                "save_app_2_market",
                                "Export to q2Market",
                                control="button",
                                # datalen=14,
                                valid=self.export_q2market,
                                style="background:LightCoral; ; font-weight:bold",
                            )
                        self.add_control("/")

                    self.add_control("/s")

                    if self.add_control("/h", "Import"):
                        self.add_control(
                            "load_app",
                            "From JSON file",
                            control="button",
                            mess="Excluding _ prefixes",
                            # datalen=10,
                            valid=self.import_app,
                        )
                        self.add_control(
                            "load_app_all",
                            "From JSON file *",
                            mess="Import all, including _ prefixes",
                            control="button",
                            # datalen=10,
                            valid=self.import_app_all,
                            style="background:#FF6666; font-weight:bold",
                        )
                        if self.q2_app.app_url:
                            self.add_control(
                                "load_q2market_app",
                                "From q2Market",
                                control="button",
                                # datalen=10,
                                valid=self.import_q2market,
                            )
                        self.add_control("/")

                    self.add_control("/")

            self.add_control("/")

        if self.add_control("/v", "Data"):
            if self.add_control("/h", "Database"):
                self.add_control(
                    "drd",
                    "Type",
                    data=app_data["driver_data"].lower(),
                    readonly=1,
                    datalen=len(app_data["driver_data"].strip()) + 5,
                )
                self.add_control(
                    "dtd",
                    "Name ",
                    data=app_data["database_data"],
                    readonly=1,
                    datalen=len(app_data["database_data"].strip()),
                )
                if app_data.get("host_data"):
                    self.add_control(
                        "hd",
                        "Host",
                        data=app_data["host_data"],
                        readonly=1,
                        datalen=len(app_data["host_data"].strip()),
                    )
                if num(app_data.get("port_data")):
                    self.add_control(
                        "pd",
                        "Port",
                        data=app_data["port_data"],
                        readonly=1,
                        datalen=len(f"{app_data['port_data']}") + 5,
                    )
                self.add_control("/s")
                self.add_control("/")

            if self.add_control("/h", ""):
                if self.add_control("/h", "Export"):
                    self.add_control(
                        "save_data",
                        "As JSON file",
                        control="button",
                        datalen=10,
                        valid=self.export_data,
                    )
                    self.add_control("/")
                self.add_control("/s")
                if self.add_control("/h", "Import"):
                    self.add_control(
                        "load_app",
                        "From JSON file",
                        control="button",
                        datalen=10,
                        valid=self.import_data,
                    )
                    self.add_control("/")
                self.add_control("/")
            self.add_control("/")

        self.cancel_button = 1

    def reinstall(self):
        if q2ask("You are about to reinstall platform packages?") == 2:
            # q2app.q2_app.update_packages(force=True)
            q2app.q2_app.update_from_git(source="")

    def update_from_git(self):
        if q2ask("You are about to reinstall platform packages from github.com! Are you sure?") == 2:
            q2app.q2_app.update_from_git()

    def reload_assets(self):
        q2app.q2_app.load_assets(True)

    def export_q2market(self):
        self.q2_app.run_module("manifest")
        if not self.q2_app.app_url:
            q2Mess("No App URL!")
            return
        if (
            q2AskYN(
                "<p>You are about to export App "
                f"<p>into folder {os.path.abspath(self.q2_app.q2market_path)}"
                "<p>Are you sure?"
            )
            != 2
        ):
            return

        version = datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")
        version_line = f"self.app_version = '{version}'"
        app_name = os.path.basename(self.q2_app.app_url)
        q2market_file = f"{self.q2_app.q2market_path}/q2market.json"
        if os.path.isfile(q2market_file):
            q2market = json.load(open(q2market_file))
        else:
            q2market = {}
        q2market[self.q2_app.app_url] = {
            "app_title": self.q2_app.app_title,
            "app_version": version,
            "app_description": self.q2_app.app_description,
        }
        json.dump(q2market, open(q2market_file, "w"), indent=2)
        open(f"{self.q2_app.q2market_path}/{app_name}.version", "w").write(version)

        if get("modules", "name='version'", q2_db=self.q2_app.db_logic):
            update("modules", {"name": "version", "script": version_line}, q2app.q2_app.db_logic)
        else:
            insert("modules", {"name": "version", "script": version_line}, q2app.q2_app.db_logic)
        self.q2_app.run_module("version")

        app_json = self.get_app_json()

        self.export_app(f"{self.q2_app.q2market_path}/{app_name}.json", app_json)
        if app_name == "demo_app":
            self.export_data(f"{self.q2_app.q2market_path}/demo_data.json")

        if os.path.isdir(f"{self.q2_app.q2market_path}/.git"):
            trm = Q2Terminal(callback=print)

            def worker():
                trm.run(f"cd {self.q2_app.q2market_path}")
                trm.run("git add -A")
                trm.run(f"""git commit -a -m"{version}"  """)

            q2working(worker, "Commiting")
            q2Mess(trm.run("""git push"""))
            trm.close()
        else:  # try FTP
            if os.path.isfile(".ftp"):
                login, password = open(".ftp").read().split("\n")
            else:
                login, password = (
                    "",
                    "",
                )

            app_file = f"{self.q2_app.q2market_path}/{os.path.basename(self.q2_app.app_url)}"
            app_file_json = f"{app_file}.json"
            app_file_version = f"{app_file}.version"
            server = urlparse(self.q2_app.app_url).netloc
            if server in self.q2_app.app_url:
                workdir = os.path.dirname(self.q2_app.app_url.split(server)[1])
            else:
                workdir = ""
            ftp_creds = Q2Form("FTP credentials")
            ftp_creds.add_control("server", "Server", datalen=100, data=server)
            ftp_creds.add_control("login", "Login", datalen=100, data=login)
            ftp_creds.add_control("password", "Password", pic="*", datalen=100, data=password)
            ftp_creds.ok_button = 1
            ftp_creds.cancel_button = 1
            ftp_creds.run()
            if ftp_creds.ok_pressed:
                try:
                    ftp_upload([app_file_json, app_file_version], server, workdir, login, password)
                except Exception as error:
                    q2Mess(f"Error while uploading: {error}")

    def export_app(self, file="", app_json=None):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_save_file_dialoq("Export Application", filter=filetype)
        if not file:
            return
        file = self.validate_impexp_file_name(file, filetype)
        if file:
            if app_json is None:
                app_json = q2working(self.get_app_json, "Prepare data...")
            if app_json:
                json.dump(app_json, open(file, "w"), indent=1)

    def get_app_json(self):
        return AppManager._get_app_json()

    @staticmethod
    def _get_app_json(prefix=""):
        db: Q2Db = q2app.q2_app.db_logic
        rez = {}
        for table in db.get_tables():
            if table not in app_tables:
                continue
            if table.startswith("log_") or table == "sqlite_sequence":
                continue
            rez[table] = []
            for row in db.table(table).records():
                if prefix:
                    if table != "packages" and not row.get("name").startswith(prefix):
                        continue
                rez[table].append(row)
        return rez

    def tables_selector(self, mode="export"):
        st = Q2Form(f"Select tables for {mode}")
        st.ok_button = 1
        st.cancel_button = 1

        def get_widgets(st=st):
            return [x for x in st.widgets() if x.startswith("c_")]

        tables = [
            x
            for x in q2app.q2_app.db_data.get_tables()
            if not x.startswith("log_") and x != "sqlite_sequence"
        ]
        if st.add_control("/v"):
            if st.add_control("/vr"):
                tables.sort()
                for index, table in enumerate(tables):
                    if self.selected_tables == []:
                        check_data = 1
                    else:
                        check_data = table in self.selected_tables

                    label = get("forms", f"form_table='{table}'", "title", self.q2_app.db_logic)
                    st.add_control(
                        f"c_{index}", pic=f"{table} ({label})", control="check", data=check_data, stretch=99
                    )
            st.add_control("/")
        st.add_control("/")
        st.add_control("/h")
        st.add_control(
            "all",
            "Check all",
            control="button",
            datalen=10,
            valid=lambda: [st.s.__setattr__(x, 1) for x in get_widgets()],
        )
        st.add_control(
            "nothing",
            "Uncheck all",
            control="button",
            datalen=10,
            valid=lambda: [st.s.__setattr__(x, 0) for x in get_widgets()],
        )
        st.add_control(
            "invert",
            "Invert",
            control="button",
            datalen=10,
            valid=lambda: [st.s.__setattr__(x, 0 if st.s.__getattr__(x) else 1) for x in get_widgets()],
        )
        st.add_control("/")
        st.run()

        if st.ok_pressed:
            self.selected_tables = [
                table for index, table in enumerate(tables) if st.s.__getattr__(f"c_{index}")
            ]
            return True

    def export_data(self, file=""):
        if not self.tables_selector("export"):
            return
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_save_file_dialoq("Export Database", filter=filetype)

        if not file:
            return

        file = self.validate_impexp_file_name(file, filetype)
        if file:
            rez = q2working(self.get_data_json, "Prepare data...")
            if rez:
                json.dump(rez, open(file, "w"), indent=1)

    def get_data_json(self):
        db: Q2Db = q2app.q2_app.db_data
        rez = {}
        for table in db.get_tables():
            if table in app_tables:
                continue
            if table.startswith("log_") or table == "sqlite_sequence":
                continue
            if table not in self.selected_tables:
                continue
            rez[table] = []
            for row in db.table(table).records():
                rez[table].append(row)
        return rez

    def import_q2market(self):
        if self.q2_app.check_app_update(force_update=True):
            self.q2_app.open_selected_app()

    def import_app(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq("Import Application", filter=filetype)

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        self.import_json_app(data)
        # self.q2_app.migrate_db_data()
        self.q2_app.open_selected_app()

    def import_app_all(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq("Import Application", filter=filetype)

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        self.import_json_app(data, prefix="*")
        # self.q2_app.migrate_db_data()
        self.q2_app.open_selected_app()

    @staticmethod
    def import_json_app(data, db=None, prefix=""):
        if db is None:
            db: Q2Db = q2app.q2_app.db_logic
        db_tables = db.get_tables()
        wait_table = Q2WaitShow(len(data))
        errors = []
        db.transaction()
        for table in sorted(data, key=lambda k: "" if k == "forms" else k):
            wait_table.step(table)
            if table not in db_tables:
                continue
            wait_row = Q2WaitShow(len(data[table]))
            if table != "packages":
                if prefix == "*":
                    db.cursor(f"delete from `{table}`")
                elif prefix:
                    db.cursor(f'delete from `{table}` where substr(name,1,{len(prefix)}) = "{prefix}"')
                else:
                    db.cursor(f'delete from `{table}` where substr(name,1,1) <> "_"')
            if db.last_sql_error:
                errors.append(db.last_sql_error)
            for row in data[table]:
                wait_row.step()
                if table == "packages":
                    if (
                        get("packages", "package_name='%s'" % row["package_name"], "package_name", db)
                        == row["package_name"]
                    ):
                        continue
                else:
                    if prefix == "*":
                        pass
                    elif prefix:
                        if not row.get("name").startswith(prefix):
                            continue
                    else:
                        if row.get("name", "").startswith("_"):
                            continue
                if not db.insert(table, row):
                    errors.append(db.last_sql_error)
                    errors.append(db.last_record)
            wait_row.close()
        db.commit()
        wait_table.close()
        if errors:
            q2Mess("<br>".join(errors))

    def import_data(self, file=""):
        if not self.tables_selector("import"):
            return
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq("Import Data", filter=filetype)

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        self.import_json_data(data, self.selected_tables)

    @staticmethod
    def import_json_data(data, selected_tables=[]):
        db: Q2Db = q2app.q2_app.db_data
        db_tables = db.get_tables()
        wait_table = Q2WaitShow(len(data))
        db.transaction()
        errors = []
        for table in data:
            wait_table.step(table)
            if table not in db_tables:
                continue
            if selected_tables and table not in selected_tables:
                continue
            wait_row = Q2WaitShow(len(data[table]))
            db.cursor(f"delete from {table}")
            for row in data[table]:
                wait_row.step()
                if not db.raw_insert(table, row):
                    errors.append(db.last_sql_error)
                    # print(db.last_sql_error)
            wait_row.close()
        db.commit()
        wait_table.close()
        if errors:
            q2Mess("<br>".join(errors))
