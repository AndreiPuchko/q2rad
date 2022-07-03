if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.db import Q2Db
from q2gui.q2utils import num
from q2gui import q2app
from q2gui.q2dialogs import q2AskYN

from q2rad import Q2Form


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
                        datalen=10,
                        valid=self.export_app,
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

    def export_app(self, file=""):
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_save_file_dialoq(
                "Export Application", filter=filetype
            )

        if not file:
            return

        file = self.validate_impexp_file_name(file, filetype)
        if file:
            db: Q2Db = q2app.q2_app.db_logic
            rez = {}
            for x in db.get_tables():
                if x.startswith("log_"):
                    continue
                rez[x] = []
                for row in db.table(x).records():
                    rez[x].append(row)

            if rez:
                json.dump(rez, open(file, "w"), indent=1)

    def export_demo_data(self):
        if q2AskYN("Are you sure") != 2:
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
