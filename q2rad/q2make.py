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
import zipfile
from q2terminal.q2terminal import Q2Terminal
from q2rad.q2utils import q2cursor, Q2Form, open_folder  # noqa F401
from q2gui.q2dialogs import q2mess, q2wait, q2ask
from q2rad.q2appselector import Q2AppSelect
from q2db.db import Q2Db
from q2rad.q2appmanager import AppManager
from q2gui import q2app


def create_q2apps_sqlite(dist_folder):
    database_folder_name = "databases"
    appsel = Q2AppSelect(f"{dist_folder}/q2apps.sqlite")
    database_name_prefix = os.path.basename(appsel.q2_app.app_url) if appsel.q2_app.app_url else "app1"
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
    db_logic.close()
    db_logic = None


def make_binary(self):
    form = Q2Form()
    form.add_control("make_folder", "Working folder", datatype="char", data="make")
    form.add_control(
        "binary_name",
        "Application name",
        datatype="char",
        data=os.path.basename(q2app.q2_app.app_url) if q2app.q2_app.app_url else "q2-app",
    )
    # form.add_control("onefile", "One file", datatype="char", control="check")
    form.ok_button = 1
    form.cancel_button = 1
    form.show_form("Build binary")
    if not form.ok_pressed:
        return

    if q2ask("Уou are about to start building binary executable file of Q2RAD!<br>Are You Sure?") != 2:
        return

    make_folder = os.path.abspath(form.s.make_folder)
    binary_name = form.s.binary_name
    # onefile = "--onefile" if form.s.onefile else ""
    onefile = ""
    if not os.path.isdir(make_folder):
        os.mkdir(make_folder)
    if not os.path.isdir(make_folder):
        return

    main = """
import sys
if "darwin" in sys.platform:
    path = sys.argv[0].split("/Contents/MacOS")[0]
    path = os.path.dirname(path)
    os.chdir(path)

from q2rad.q2rad import Q2RadApp
app = Q2RadApp()
app.run()
    """
    open(f"{make_folder}/{binary_name}.py", "w").write(main)

    dist_folder = os.path.abspath(f"{make_folder}/dist/{binary_name}")

    terminal = Q2Terminal(callback=print)
    pynstaller_executable = f"'{sys.executable.replace('w.exe', '.exe')}' -m PyInstaller"
    if "win32" in sys.platform:
        pynstaller_executable = "& " + pynstaller_executable
    if not os.path.isfile("poetry.lock"):
        terminal.run(f"{pynstaller_executable} -v")
        if terminal.exit_code != 0:
            terminal.run(f"'{sys.executable.replace('w.exe', '.exe')}' -m pip install pyinstaller")
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
    terminal.run(f"cd '{make_folder}'")
    w = q2wait()
    if not os.path.isfile(os.path.abspath(f"{make_folder}/q2rad.ico")):
        shutil.copy("assets/q2rad.ico", os.path.abspath(f"{make_folder}/q2rad.ico"))
    # run pyinstaller
    terminal.run(
        f"{pynstaller_executable} -y --noconsole --clean {onefile} "
        f" {packages} -i q2rad.ico '{binary_name}.py'"
    )
    if not os.path.isdir(os.path.abspath(f"{dist_folder}/assets")):
        shutil.copytree("assets", os.path.abspath(f"{dist_folder}/assets"))
    create_q2apps_sqlite(f"{dist_folder}")

    # if onefile:
    #     dist_folder = os.path.abspath(f"{make_folder}/dist")
    #     for x in os.listdir(dist_folder):
    #         if os.path.isfile(os.path.join(dist_folder, x)):
    #             shutil.move(os.path.join(dist_folder, x), os.path.join(dist_folder, binary_name, x))

    if "darwin" in sys.platform:
        shutil.move(
            f"{make_folder}/dist/{binary_name}.app", f"{make_folder}/dist/{binary_name}/{binary_name}.app"
        )
        os.remove(f"{make_folder}/dist/{binary_name}/{binary_name}")
        shutil.rmtree(f"{make_folder}/dist/{binary_name}/_internal", ignore_errors=True)

    name = f"{make_folder}/dist/{binary_name}"
    zip_name = name + ".zip"

    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zip_ref:
        for folder_name, subfolders, filenames in os.walk(name):
            for filename in filenames:
                file_path = os.path.join(folder_name, filename)
                zip_ref.write(file_path, arcname=f"{binary_name}/{os.path.relpath(file_path, name)}")

    zip_ref.close()

    w.close()

    if terminal.exit_code != 0:
        q2mess("Error occured while making binary! See output for details.")
    else:
        if (
            q2ask(
                f"Success! You binary is located in <b>{dist_folder}</b> <br>Do you want to open the folder?"
            )
            == 2
        ):
            open_folder(dist_folder)
    terminal.close()
