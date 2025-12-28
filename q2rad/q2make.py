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
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


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
    appsel.db.close()


def create_q2apps_mysql(dist_folder):
    database_folder_name = "databases"
    appsel = Q2AppSelect(f"{dist_folder}/q2apps.sqlite")
    database_name_prefix = os.path.basename(appsel.q2_app.app_url) if appsel.q2_app.app_url else "app1"
    appsel.db.insert(
        "applications",
        {
            "ordnum": 1,
            "name": appsel.q2_app.app_title,
            "driver_data": "mysql",
            "database_data": f"{database_name_prefix}_data",
            "port_data": f"{appsel.q2_app.windows_mysql_local_server_default_port}",
            "driver_logic": "mysql",
            "database_logic": f"{database_name_prefix}_logic",
            "port_logic": f"{appsel.q2_app.windows_mysql_local_server_default_port}",
            "autoselect": "*",
            "dev_mode": "",
        },
    )

    from q2mysql55_win_local.server import Q2MySQL55_Win_Local_Server

    mysql3388_datadir = os.path.join(dist_folder, appsel.q2_app.windows_mysql_local_server_datadir)
    mysql3388server = Q2MySQL55_Win_Local_Server()
    mysql3388server.start(3388, mysql3388_datadir)
    db_logic = Q2Db(
        "mysql",
        user="q2user",
        password="q2password",
        port=3388,
        database_name=f"{database_name_prefix}_logic",
        root_user="root",
        root_password="",
    )
    db_logic.get_admin_credential_callback = lambda: ["root", ""]
    appsel.q2_app.migrate_db_logic(db_logic)

    db_data = Q2Db(
        "mysql",
        user="q2user",
        password="q2password",
        port=3388,
        database_name=f"{database_name_prefix}_data",
        root_user="root",
        root_password="",
    )
    db_data.close()

    AppManager().import_json_app(AppManager().get_app_json(), db_logic)
    db_logic.close()
    mysql3388server.stop()
    db_logic = None
    appsel.db.close()


def make_binary(self):
    print("Prepare make")
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
    _logger.info("Binary building started")
    make_folder = os.path.abspath(form.s.make_folder)
    binary_name = form.s.binary_name
    # onefile = "--onefile" if form.s.onefile else ""
    onefile = ""
    if not os.path.isdir(make_folder):
        os.mkdir(make_folder)
    if not os.path.isdir(make_folder):
        return
    binary_build = f"{datetime.now()}"
    binary_url = f"{q2app.q2_app.binary_url}"

    get_packages_sql = """select package_name as name
                    from packages
                    where 'pyinstaller'<>package_name
                        and 'q2sfx'<>package_name
                    """

    packages = " ".join(
        [f"\nimport {x['name']}" for x in q2cursor(get_packages_sql, self.db_logic).records()]
    )

    main = f"""
import sys
if "darwin" in sys.platform:
    path = sys.argv[0].split("/Contents/MacOS")[0]
    path = os.path.dirname(path)
    os.chdir(path)

from q2rad.q2rad import Q2RadApp
{packages}
app = Q2RadApp()
app.binary_build = "{binary_build}"
app.binary_url = "{binary_url}"
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
        [f" --collect-data {x['name']}" for x in q2cursor(get_packages_sql, self.db_logic).records()]
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

    if (
        sys.platform == "win32"
        and q2app.q2_app.windows_mysql_local_server
        and q2app.q2_app.windows_mysql_local_server.is_running()
    ):
        create_q2apps_mysql(f"{dist_folder}")
    else:
        create_q2apps_sqlite(f"{dist_folder}")

    if "darwin" in sys.platform:
        shutil.move(
            f"{make_folder}/dist/{binary_name}.app", f"{make_folder}/dist/{binary_name}/{binary_name}.app"
        )
        os.remove(f"{make_folder}/dist/{binary_name}/{binary_name}")
        shutil.rmtree(f"{make_folder}/dist/{binary_name}/_internal", ignore_errors=True)

    from q2sfx import Q2SFXBuilder

    print(f"Building {make_folder}/dist/{binary_name}_sfx.exe")
    Q2SFXBuilder.build_sfx_from(
        # payload_zip=zip_name,
        dist_path=f"{make_folder}/dist/{binary_name}",
        dist_zip_dir=f"{make_folder}/dist.zip/{binary_name}",
        output_dir=f"{make_folder}/dist.sfx",
        output_name=f"{binary_name}_sfx.exe",
        build_time=binary_build,
    )

    w.close()
    print("Done")

    if terminal.exit_code != 0:
        q2mess("Error occured while making binary! See output for details.")
    else:
        if (
            q2ask(
                f"Success! You binary is located in <b>{dist_folder}</b><br>Do you want to open the folder?"
            )
            == 2
        ):
            open_folder(dist_folder)
    terminal.close()
