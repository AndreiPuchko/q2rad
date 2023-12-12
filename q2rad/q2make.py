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

import os
import sys
import shutil
from q2terminal.q2terminal import Q2Terminal
from q2rad.q2utils import Q2Form, open_folder  # noqa F401
from q2rad.q2raddb import q2cursor
from q2gui.q2dialogs import q2mess, q2wait, q2ask
from q2rad.q2appselector import Q2AppSelect
from q2db.db import Q2Db
from q2rad.q2appmanager import AppManager


def create_q2apps_sqlite(dist_folder):
    database_folder_name = "databases"
    database_name_prefix = "app1"
    appsel = Q2AppSelect(f"{dist_folder}/q2apps.sqlite")
    appsel.db.insert(
        "applications",
        {
            "ordnum": 1,
            "name": appsel.q2_app.app_title,
            "driver_data": "Sqlite",
            "database_data": f"{database_folder_name}/{database_name_prefix}_data_storage.sqlite",
            "driver_logic": "Sqlite",
            "database_logic": f"{database_folder_name}/{database_name_prefix}_logic_storage.sqlite",
            "autoselect": "*",
            "dev_mode": "",
        },
    )
    dababase_folder = f"{dist_folder}/{database_folder_name}"
    if not os.path.isdir(dababase_folder):
        os.mkdir(dababase_folder)
    db_logic = Q2Db(
        database_name=os.path.abspath(f"{dababase_folder}/{database_name_prefix}_logic_storage.sqlite")
    )
    appsel.q2_app.migrate_db_logic(db_logic)
    AppManager().import_json_app(AppManager().get_app_json(), db_logic)


def make_binary(self):
    form = Q2Form()
    form.add_control("make_folder", "Working folder", datatype="char", data="make")
    form.add_control("binary_name", "Application name", datatype="char", data="q2-app")
    form.ok_button = 1
    form.cancel_button = 1
    form.show_form("Build binary")
    if not form.ok_pressed:
        return

    if q2ask("Are you about to start buiding binary executable file of Q2RAD!<br>Are You Sure?") != 2:
        return

    make_folder = os.path.abspath(form.s.make_folder)
    binary_name = form.s.binary_name
    if not os.path.isdir(make_folder):
        os.mkdir(make_folder)
    if not os.path.isdir(make_folder):
        return

    main = "from q2rad.q2rad import Q2RadApp;app = Q2RadApp();app.run()"
    open(f"{make_folder}/{binary_name}.py", "w").write(main)

    dist_folder = os.path.abspath(f"{make_folder}\\dist\\{binary_name}")

    terminal = Q2Terminal(callback=print)
    pynstaller_executable = os.path.dirname(sys.executable) + "/pyinstaller"

    if not os.path.isfile("poetry.lock"):
        terminal.run(f"{pynstaller_executable} -v")
        if terminal.exit_code != 0:
            pip_executable = os.path.dirname(sys.executable) + "/pip"
            terminal.run(f"{pip_executable} install pyinstaller")
            if terminal.exit_code != 0:
                q2mess("Pyinstaller not installed!")
                return

    packages = " ".join(
        [
            f" --collect-all {x['name']}"
            for x in q2cursor(
                "select package_name as name from packages where 'pyinstaller'<>package_name ",
                self.db_logic,
            ).records()
        ]
    )
    packages += " --collect-all pip "
    terminal.run(f"cd {make_folder}")
    w = q2wait()
    if not os.path.isfile(os.path.abspath(f"{make_folder}/q2rad.ico")):
        shutil.copy("assets/q2rad.ico", os.path.abspath(f"{make_folder}/q2rad.ico"))
    # run pyinstaller
    terminal.run(f"{pynstaller_executable} -y --noconsole {packages} -i q2rad.ico {binary_name}.py")

    if not os.path.isdir(os.path.abspath(f"{dist_folder}/assets")):
        shutil.copytree("assets", os.path.abspath(f"{dist_folder}/assets"))
    create_q2apps_sqlite(f"{dist_folder}")

    w.close()

    if terminal.exit_code != 0:
        q2mess("Error occured while making binary! See output for details.")
    else:
        if q2ask(f"Success! You binary is located in <b>{dist_folder}</b> <br>Are You Sure?") == 2:
            open_folder(dist_folder)
    terminal.close()
