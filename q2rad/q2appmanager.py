if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.db import Q2Db
from q2gui.q2utils import num
from q2gui import q2app
from q2gui.q2dialogs import q2AskYN, q2Mess

from q2rad import Q2Form
from datetime import datetime

import json
import os


class AppManager(Q2Form):
    def __init__(self, title=""):
        super().__init__("Manage q2Application")

    def on_init(self):
        app_data = q2app.q2_app.selected_application
        self.add_control("/")
        if self.add_control("/h", "Platform"):
            self.add_control(
                "upgrade",
                "Update",
                control="button",
                datalen=10,
                valid=q2app.q2_app.update_packages,
            )

            self.add_control(
                "reload_assets",
                "Reload assets",
                control="button",
                datalen=10,
                valid=self.reload_assets,
            )

            self.add_control("/")

        if self.add_control("/v", "Application"):
            if self.add_control("/f", ""):
                self.add_control(
                    "drl",
                    "Database type",
                    data=app_data["driver_logic"],
                    disabled=1,
                    datalen=len(app_data["driver_logic"].strip()),
                )
                self.add_control(
                    "dtl",
                    "Database name ",
                    data=app_data["database_logic"],
                    disabled=1,
                    datalen=len(app_data["database_logic"].strip()),
                )
                if app_data.get("host_logic"):
                    self.add_control(
                        "hl",
                        "Host",
                        data=app_data["host_logic"],
                        disabled=1,
                        datalen=len(app_data["host_logic"].strip()),
                    )
                if num(app_data.get("port_logic")):
                    self.add_control(
                        "pl",
                        "Port",
                        data=app_data["port_logic"],
                        disabled=1,
                        datalen=len(app_data["port_logic"]) + 5,
                    )
                self.add_control("/")

            if self.add_control("/h", ""):
                if self.add_control("/h", "Export"):
                    self.add_control(
                        "save_app",
                        "As JSON file",
                        control="button",
                        datalen=13,
                        valid=self.export_app,
                    )
                    self.add_control(
                        "save_app_2_market",
                        "Export to q2Market",
                        control="button",
                        datalen=14,
                        valid=self.export_q2market,
                    )
                    self.add_control("/")
                if self.add_control("/h", "Import"):
                    self.add_control(
                        "load_app",
                        "From JSON file",
                        control="button",
                        datalen=10,
                        valid=self.import_app,
                    )
                    self.add_control("/")
                self.add_control("/")

            self.add_control("/")

        if self.add_control("/v", "Data"):
            if self.add_control("/f", ""):
                self.add_control(
                    "drd",
                    "Database type",
                    data=app_data["driver_data"],
                    disabled=1,
                    datalen=len(app_data["driver_data"].strip()),
                )
                self.add_control(
                    "dtd",
                    "Database name ",
                    data=app_data["database_data"],
                    disabled=1,
                    datalen=len(app_data["database_data"].strip()),
                )
                if app_data.get("host_data"):
                    self.add_control(
                        "hd",
                        "Host",
                        data=app_data["host_data"],
                        disabled=1,
                        datalen=len(app_data["host_data"].strip()),
                    )
                if num(app_data.get("port_data")):
                    self.add_control(
                        "pd",
                        "Port",
                        data=app_data["port_data"],
                        disabled=1,
                        datalen=len(app_data["port_data"]) + 5,
                    )
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

        # if self.q2_app.dev_mode:
        if os.path.isfile("poetry.lock"):
            if self.add_control("/h", "Demo Application"):
                self.add_control(
                    "save_demo_app",
                    "Export Application",
                    mess="Write to demo_app/demo_app.json",
                    control="button",
                    datalen=10,
                    valid=self.export_demo_app,
                )
                self.add_control(
                    "save_demo_data",
                    "Export Data",
                    mess="Write to demo_app/demo_data.json",
                    control="button",
                    datalen=10,
                    valid=self.export_demo_data,
                )
                self.add_control("/")
        self.cancel_button = 1

    def reload_assets(self):
        q2app.q2_app.load_assets(True)

    def export_demo_app(self):
        if q2AskYN("Are you sure") != 2:
            return
        if not os.path.isdir("demo_app"):
            os.mkdir("demo_app")
        self.export_app("demo_app/demo_app.json")

    def export_q2market(self):
        if not self.q2_app.app_url:
            q2Mess("No App URL!")
            return
        version = datetime.now().strftime(r"%Y-%m-%d %H:%M:%S")
        app_name = os.path.basename(self.q2_app.app_url)
        if 0 and (
            q2AskYN(
                "Do you really want to save App <br>"
                f"<b>{app_name}</b>"
                f"(<font color=blue>{self.q2_app.app_title}</font>)<br>"
                " to the q2Market?"
            )
            != 2
        ):
            return
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
        app_json = self.get_app_json()

        modules = app_json.get("modules")
        if modules:
            for row, dic in enumerate(modules):
                if dic["name"] == "autorun":
                    modules[row]["script"] = f"myapp.app_version     = '{version}'\n" + modules[row]["script"]

        self.export_app(f"{self.q2_app.q2market_path}/{app_name}.json", app_json)

    def export_app(self, file="", app_json=None):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_save_file_dialoq(
                "Export Application", filter=filetype
            )
        if not file:
            return
        file = self.validate_impexp_file_name(file, filetype)
        if file:
            if app_json is None:
                app_json = self.get_app_json()
            if app_json:
                json.dump(app_json, open(file, "w"), indent=1)

    def get_app_json(self):
        db: Q2Db = q2app.q2_app.db_logic
        rez = {}
        for x in db.get_tables():
            if x.startswith("log_"):
                continue
            rez[x] = []
            for row in db.table(x).records():
                rez[x].append(row)
        return rez

    def export_demo_data(self):
        if q2AskYN("Are you sure?") != 2:
            return
        if not os.path.isdir("demo_app"):
            os.mkdir("demo_app")
        self.export_data("demo_app/demo_data.json")

    def export_data(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_save_file_dialoq(
                "Export Database", filter=filetype
            )

        if not file:
            return

        file = self.validate_impexp_file_name(file, filetype)
        if file:
            db: Q2Db = q2app.q2_app.db_data
            rez = {}
            for x in db.get_tables():
                if x.startswith("log_"):
                    continue
                rez[x] = []
                for row in db.table(x).records():
                    rez[x].append(row)

            if rez:
                json.dump(rez, open(file, "w"), indent=1)

    def import_app(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq(
                "Import Application", filter=filetype
            )

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        self.import_json_app(data)
        self.q2_app.migrate_db_data()

    @staticmethod
    def import_json_app(data):
        db: Q2Db = q2app.q2_app.db_logic
        for table in data:
            db.cursor(f"delete from {table}")
            for row in data[table]:
                if not db.raw_insert(table, row):
                    print(db.last_sql_error)

    def import_data(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq(
                "Import Data", filter=filetype
            )

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        self.import_json_data(data)

    @staticmethod
    def import_json_data(data):
        db: Q2Db = q2app.q2_app.db_data
        for table in data:
            db.cursor(f"delete from {table}")
            for row in data[table]:
                if not db.raw_insert(table, row):
                    print(db.last_sql_error)
