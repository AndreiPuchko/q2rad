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
from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2utils import num
from q2gui import q2app
from q2gui.q2dialogs import q2AskYN, q2Mess, Q2WaitShow, q2ask, q2working

from q2rad import Q2Form
from q2terminal.q2terminal import Q2Terminal
from q2rad.q2raddb import insert, update, get, last_error, delete
from datetime import datetime
from urllib.parse import urlparse
from q2rad.q2utils import ftp_upload

import json
import os
import gzip
import base64

from q2rad.q2utils import tr

_ = tr

app_tables = [
    "forms",
    "lines",
    "actions",
    "reports",
    "modules",
    "queries",
    "packages",
    "locale",
    "locale_po",
]


def clean_json(data):
    if isinstance(data, dict):
        return {
            k: clean_json(v)
            for k, v in data.items()
            if v not in ("", "0")
            and not k.startswith("q2_mode")
            and not k.startswith("q2_time")
            and k != "id"
        }
    elif isinstance(data, list):
        return [clean_json(item) for item in data]
    return data


def encode_json(data):
    """Converts a Python object into a gzip+Base64 string.."""
    json_bytes = json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(json_bytes)
    return base64.b64encode(compressed).decode("ascii")


def decode_json(text):
    """Restores a Python object from a gzip+Base64 string."""
    compressed = base64.b64decode(text.encode("ascii"))
    json_bytes = gzip.decompress(compressed)
    return json.loads(json_bytes.decode("utf-8"))


class AppManager(Q2Form):
    def __init__(self, title=""):
        super().__init__(_("Manage q2Application"))
        self.selected_tables = []

    def on_init(self):
        app_data = q2app.q2_app.selected_application
        frozen = q2app.q2_app.frozen
        # frozen = 1

        self.add_control("/")
        if not frozen:
            if self.add_control("/h", _("Platform")):
                if not q2app.q2_app.frozen:
                    self.add_control(
                        "upgrade",
                        _("Check updates"),
                        control="button",
                        valid=q2app.q2_app.update_packages,
                    )

                    self.add_control("/s")

                    self.add_control(
                        "reinstall_",
                        _("Reinstall"),
                        control="button",
                        valid=self.reinstall,
                    )

                    self.add_control(
                        "reinstall_git",
                        _("Reinstall from GitHub"),
                        control="button",
                        valid=self.update_from_git,
                    )

                    self.add_control("/s")

                self.add_control(
                    "reload_assets",
                    _("Reload assets"),
                    control="button",
                    valid=self.reload_assets,
                )

                self.add_control("/")

        if self.add_control("/v", _("Application")):
            if self.add_control("/f"):
                self.add_control(
                    "",
                    _("App title"),
                    control="line",
                    data=q2app.q2_app.app_title,
                    readonly=1,
                )
                if not frozen and q2app.q2_app.app_url:
                    self.add_control(
                        "",
                        _("App URL"),
                        control="line",
                        data=q2app.q2_app.app_url,
                        readonly=1,
                    )
                if q2app.q2_app.app_version:
                    self.add_control(
                        "",
                        _("App version"),
                        control="line",
                        data=q2app.q2_app.app_version,
                        readonly=1,
                    )
                self.add_control("/")

            if not frozen:
                if self.add_control("/h", _("Database"), alignment=7):
                    self.add_control(
                        "drl",
                        _("Type"),
                        data=app_data["driver_logic"].lower(),
                        readonly=1,
                        datalen=len(app_data["driver_logic"].strip()) + 5,
                    )
                    self.add_control(
                        "dtl",
                        _("Name"),
                        data=app_data["database_logic"],
                        readonly=1,
                        datalen=len(app_data["database_logic"].strip()),
                        stretch=99,
                    )
                    if app_data.get("host_logic"):
                        self.add_control(
                            "hl",
                            _("Host"),
                            data=app_data["host_logic"],
                            readonly=1,
                            datalen=len(app_data["host_logic"].strip()),
                        )
                    if num(app_data.get("port_logic")):
                        self.add_control(
                            "pl",
                            _("Port"),
                            data=app_data["port_logic"],
                            readonly=1,
                            datalen=len(f"{app_data['port_logic']}") + 5,
                        )
                    self.add_control("/s")
                    self.add_control("/")

                if self.add_control("/h", ""):
                    self.add_control("/h", _("Open"))
                    self.add_control(
                        "exts",
                        _("Extensions"),
                        control="button",
                        # datalen=13,
                        valid=q2app.q2_app.run_extensions,
                    )
                    self.add_control(
                        "snapshots",
                        _("Snapshots"),
                        control="button",
                        valid=q2app.q2_app.run_snapshots,
                    )
                    self.add_control("/")

                    self.add_control("/s")
                    if self.add_control("/h", _("Edit")):
                        self.add_control(
                            "show_json",
                            _("as JSON"),
                            control="button",
                            mess=_("Edit application as JSON"),
                            valid=self.app_json_editor,
                        )
                        self.add_control("/")
                    self.add_control("/s")
                    if self.add_control("/h", _("Export")):
                        self.add_control(
                            "save_app",
                            _("as JSON file"),
                            control="button",
                            # datalen=13,
                            valid=self.export_app,
                        )
                        if os.path.isdir(self.q2_app.q2market_path):
                            self.add_control(
                                "save_app_2_market",
                                _("to q2Market"),
                                control="button",
                                # datalen=14,
                                valid=self.export_q2market,
                                style="background:LightCoral; ; font-weight:bold",
                            )
                        self.add_control("/")
                    self.add_control("/s")
                    if self.add_control("/h", _("Import")):
                        self.add_control(
                            "load_app",
                            _("from JSON file"),
                            control="button",
                            mess=_("Excluding _ prefixes"),
                            # datalen=10,
                            valid=self.import_app,
                        )
                        self.add_control(
                            "load_app_all",
                            _("from JSON file *"),
                            mess=_("Import all, including _ prefixes"),
                            control="button",
                            # datalen=10,
                            valid=self.import_app_all,
                            style="background:#FF6666; font-weight:bold",
                        )
                        if self.q2_app.app_url:
                            self.add_control(
                                "load_q2market_app",
                                _("from q2Market"),
                                control="button",
                                # datalen=10,
                                valid=self.import_q2market,
                            )
                        self.add_control("/")

                    self.add_control("/")

            self.add_control("/")

        if self.add_control("/v", _("Data")):
            if self.add_control("/h", _("Database")):
                self.add_control(
                    "drd",
                    _("Type"),
                    data=app_data["driver_data"].lower(),
                    readonly=1,
                    datalen=len(app_data["driver_data"].strip()) + 5,
                )
                self.add_control(
                    "dtd",
                    _("Name "),
                    data=app_data["database_data"],
                    readonly=1,
                    datalen=len(app_data["database_data"].strip()),
                    stretch=99,
                )
                if app_data.get("host_data"):
                    self.add_control(
                        "hd",
                        _("Host"),
                        data=app_data["host_data"],
                        readonly=1,
                        datalen=len(app_data["host_data"].strip()),
                    )
                if num(app_data.get("port_data")):
                    self.add_control(
                        "pd",
                        _("Port"),
                        data=app_data["port_data"],
                        readonly=1,
                        datalen=len(f"{app_data['port_data']}") + 5,
                    )
                self.add_control("/s")
                self.add_control("/")

            if self.add_control("/h", ""):
                if self.add_control("/h", _("Export")):
                    self.add_control(
                        "save_data",
                        _("as JSON file"),
                        control="button",
                        datalen=10,
                        valid=self.export_data,
                    )
                    self.add_control("/")
                self.add_control("/s")
                if self.add_control("/h", _("Import")):
                    self.add_control(
                        "load_app",
                        _("from JSON file"),
                        control="button",
                        datalen=10,
                        valid=self.import_data,
                    )
                    self.add_control("/")
                self.add_control("/")
            self.add_control("/")

        self.cancel_button = 1

    def app_json_editor(self):
        form = Q2Form("Edit as JSON")
        app_json = q2working(AppManager._get_app_json, _("Prepare data..."))
        form.heap.app_json_text = json.dumps(clean_json(app_json), ensure_ascii=False, indent=2)

        form.add_control("/v")
        form.add_control(
            "json",
            control="code_json",
            data=form.heap.app_json_text,
        )
        form.ok_button = 1
        form.cancel_button = 1

        def json_save():
            if form.heap.app_json_text != form.s.json:
                try:
                    json_data = json.loads(form.s.json)
                except Exception as e:
                    q2Mess(
                        _(
                            "The edited text is not valid JSON. Please correct the syntax and try again."
                            + "<br><br>"
                            + f"{e}"
                        )
                    )
                    return False
                form.heap.app_json_text = form.s.json
                if q2ask(_("Do you want to create an app snapshot before applying the changes?")):
                    AppManager.make_snapshot(_("Before applying direct JSON edits"))
                self.import_json_app(json_data)
                self.q2_app.migrate_db_data()

        form.ext_system_controls.add_control(
            "go",
            _("Apply Changes"),
            control="button",
            mess=_("Apply changes without closing this window"),
            valid=json_save,
        )
        form.valid = json_save

        form.run()

    def reinstall(self):
        if q2ask(_("You are about to reinstall platform packages?")) == 2:
            # q2app.q2_app.update_packages(force=True)
            q2app.q2_app.update_from_git(source="")

    def update_from_git(self):
        if q2ask(_("You are about to reinstall platform packages from github.com! Are you sure?")) == 2:
            q2app.q2_app.update_from_git()

    def reload_assets(self):
        q2app.q2_app.make_start_helpers(True)

    def export_q2market(self):
        self.q2_app.run_module("manifest")
        if not self.q2_app.app_url:
            q2Mess(_("No App URL!"))
            return
        if (
            q2AskYN(
                _("<p>You are about to export App ")
                + f"<p>into folder {os.path.abspath(self.q2_app.q2market_path)}"
                + _("<p>Are you sure?")
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
        for i, p in enumerate(app_json["packages"]):
            if p["dev_mode"] == "*":
                app_json["packages"].pop(i)

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
            ftp_creds = Q2Form(_("FTP credentials"))
            ftp_creds.add_control("server", _("Server"), datalen=100, data=server)
            ftp_creds.add_control("login", _("Login"), datalen=100, data=login)
            ftp_creds.add_control("password", _("Password"), pic="*", datalen=100, data=password)
            ftp_creds.ok_button = 1
            ftp_creds.cancel_button = 1
            ftp_creds.run_modal()
            if ftp_creds.ok_pressed:
                try:
                    ftp_upload([app_file_json, app_file_version], server, workdir, login, password)
                except Exception as error:
                    q2Mess(f"Error while uploading: {error}")

    def export_app(self, file="", app_json=None):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_save_file_dialoq(_("Export Application"), filter=filetype)
        if not file:
            return
        file = self.validate_impexp_file_name(file, filetype)
        if file:
            if app_json is None:
                app_json = q2working(self.get_app_json, _("Prepare data..."))
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
            _("Check all"),
            control="button",
            datalen=10,
            valid=lambda: [st.s.__setattr__(x, 1) for x in get_widgets()],
        )
        st.add_control(
            "nothing",
            _("Uncheck all"),
            control="button",
            datalen=10,
            valid=lambda: [st.s.__setattr__(x, 0) for x in get_widgets()],
        )
        st.add_control(
            "invert",
            _("Invert"),
            control="button",
            datalen=10,
            valid=lambda: [st.s.__setattr__(x, 0 if st.s.__getattr__(x) else 1) for x in get_widgets()],
        )
        st.add_control("/")
        st.run_modal()

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
            file, filetype = q2app.q2_app.get_save_file_dialoq(_("Export Database"), filter=filetype)

        if not file:
            return

        file = self.validate_impexp_file_name(file, filetype)
        if file:
            rez = q2working(self.get_data_json, _("Prepare data..."))
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
            file, filetype = q2app.q2_app.get_open_file_dialoq(_("Import Application"), filter=filetype)

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        self.import_json_app(data)
        # self.q2_app.migrate_db_data()
        self.q2_app.open_selected_app()

    def import_app_all(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq(_("Import Application"), filter=filetype)

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

        # prepare locale tables
        for lang in [x["lang"] for x in data.get("locale", {})]:
            db.cursor(f'delete from `locale` where lang="{lang}"')
            db.cursor(f'delete from `locale_po` where lang="{lang}"')

        for table in sorted(data, key=lambda k: "" if k == "forms" else k):
            wait_table.step(table)
            if table not in db_tables:
                continue
            wait_row = Q2WaitShow(len(data[table]))
            # remove old app
            if table != "packages" and table not in ["locale", "locale_po"]:
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
            file, filetype = q2app.q2_app.get_open_file_dialoq(_("Import Data"), filter=filetype)

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

    @staticmethod
    def make_snapshot(comment=""):
        app_json = encode_json(clean_json(AppManager._get_app_json()))
        snapshot = {"created_at": datetime.now().strftime(r"%Y-%m-%d %H:%M:%S"), "comment": comment}
        db = q2app.q2_app.db_logic
        insert("snapshots", snapshot, q2_db=db)
        insert("snapshot_data", {"snapshot_id": snapshot["id"], "gzip_json_data": app_json}, q2_db=db)


class Q2AppSnapshots(Q2Form):
    def __init__(self, title=_("App snapshots")):
        super().__init__(title)
        self.no_view_action = True

    def before_grid_build(self):
        self.remove_action(_("Copy"))

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="snapshots", order="created_at desc")
        model = Q2CursorModel(cursor)
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("-")
        self.add_action(_("Show"), self.show_json)
        self.add_action(_("Restore"), self.restore_app)

    def create_form(self):
        self.add_control("id", "", datatype="int", pk="*", ai="*", nogrid=1, noform=1)
        self.add_control("created_at", _("Created at"), datatype="char", datalen=19)
        self.add_control("comment", _("Comment"), datatype="text")

    def restore_app(self):
        answer = q2ask(
            _("Restore app from snapshot?<br>The current state will be lost."),
            buttons=[_("Save snapshot and restore"), _("Restore only"), _("Cancel")],
        )
        if answer == 1:
            AppManager.make_snapshot(_("Before restoring snapshot"))
            self.refresh()
        if answer in [1, 2]:
            json_data = decode_json(
                get("snapshot_data", f"snapshot_id={self.r.id}", "gzip_json_data", q2_db=self.db)
            )
            AppManager.import_json_app(json_data)
            self.q2_app.migrate_db_data()

    def show_json(self):
        json_data = decode_json(
            get("snapshot_data", f"snapshot_id={self.r.id}", "gzip_json_data", q2_db=self.db)
        )
        form = Q2Form("Show JSON")
        form.add_control("/v")
        form.add_control(
            "json",
            control="code_json",
            data=json.dumps(json_data, indent=2, ensure_ascii=False),
        )
        form.cancel_button = 1
        form.run_modalless()

    def before_form_show(self):
        if self.crud_mode == "EDIT":
            self.w.created_at.set_disabled()
        else:
            self.s.created_at = datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")

    def after_crud_save(self):
        if self.crud_mode == "NEW":
            app_json = encode_json(clean_json(AppManager._get_app_json()))
            if not insert(
                "snapshot_data", {"snapshot_id": self.s.id, "gzip_json_data": app_json}, q2_db=self.db
            ):
                q2Mess(last_error(q2_db=self.db))

    def before_delete(self):
        record_to_be_deleted = self.model.get_record(self._row_to_be_deleted)
        if not delete("snapshot_data", {"snapshot_id": record_to_be_deleted["id"]}, q2_db=self.db):
            q2Mess(last_error(q2_db=self.db))


class Q2AppSnapshotsJson(Q2Form):
    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="snapshot_data", order="")
        model = Q2CursorModel(cursor)
        self.set_model(model)

    def create_form(self):
        self.add_control("id", "", datatype="int", pk="*", ai="*", nogrid=1, noform=1)
        self.add_control("snapshot_id", "", datatype="int", to_table="snapshots", to_column="id")
        self.add_control("gzip_json_data", "", datatype="longtext")
