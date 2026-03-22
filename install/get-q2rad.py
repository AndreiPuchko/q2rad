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
import urllib.request
import subprocess
from pathlib import Path
import pkgutil
import stat
import venv


RED = "\033[38;5;1m"
GREEN = "\033[38;5;2m"
YELLOW = "\033[38;5;3m"
RESET = "\033[0;0m"

code_string = "from q2rad.q2rad import main; main()"


def print_color(text="", color=None):
    print(f"{color or ''}{text}{RESET}")


# cleanup
if os.path.isfile("_tmp.py"):
    os.remove("_tmp.py")


# ensure working dir
if not os.path.isdir("q2rad"):
    os.mkdir("q2rad")

os.chdir("q2rad")


# ensure pip
if not any(x.name == "pip" for x in pkgutil.iter_modules()):
    print_color("Installing pip...", GREEN)
    try:
        gp = urllib.request.urlopen("https://bootstrap.pypa.io/get-pip.py").read()
        gp = gp.replace(b"sys.exit", b"")
        exec(gp)
    except Exception as e:
        print_color(str(e), YELLOW)
        print_color("Failed to install pip.", RED)
        sys.exit(1)


# create venv
venv_dir = Path("q2rad")

if not venv_dir.exists():
    print_color("Creating virtual environment (venv)...", GREEN)
    venv.create(venv_dir, with_pip=True)
    print_color("Done.", GREEN)


# paths
bin_folder = "Scripts" if sys.platform == "win32" else "bin"
python_bin = str(venv_dir / bin_folder / ("python.exe" if sys.platform == "win32" else "python"))


# try run
def run_app():
    return subprocess.call([python_bin, "-c", code_string])


print_color("Starting q2rad...", GREEN)

if run_app() != 0:
    print_color("Installing q2rad...", GREEN)
    subprocess.check_call(
        [
            python_bin,
            "-m",
            "pip",
            "install",
            "--upgrade",
            "--no-cache-dir",
            "q2rad",
        ]
    )

    print_color("Starting q2rad...", GREEN)
    run_app()

# create start script
project_root = Path(".").resolve()
python_bin = python_bin.replace("n.exe", "nw.exe")

if sys.platform == "win32":
    script_path = project_root / "start-q2rad.bat"
    content = f'start "" "{python_bin}" -c "{code_string}"'
else:
    script_path = project_root / "start-q2rad.sh"
    content = f'#!/bin/bash\ncd "{project_root}"\nnohup "{python_bin}" -c \'{code_string}\' &\n'

try:
    script_path.write_text(content)

    if sys.platform != "win32":
        st = os.stat(script_path)
        os.chmod(script_path, st.st_mode | stat.S_IEXEC)

    print_color(f"Start script created: {script_path}", GREEN)
except Exception as e:
    print_color(f"Failed to create start script: {e}", RED)
