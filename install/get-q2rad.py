import sys
import os
import urllib.request
import subprocess
from pathlib import Path
import shutil
import pkgutil


RED = "\033[38;5;1m"
GREEN = "\033[38;5;2m"
YELLOW = "\033[38;5;3m"
RESET = "\033[0;0m"
CLEAR = "\033[2J"

print_ = print


def print_out(text="", color=None):
    if color:
        print_(color)
    print_(text)
    print_(RESET)


print = print_out

if not os.path.isdir("q2rad"):
    os.mkdir("q2rad")
os.chdir("q2rad")

if [x.name for x in pkgutil.iter_modules() if x.name == "pip"] == []:
    print("Installing pip...", GREEN)
    try:
        gp = urllib.request.urlopen("https://bootstrap.pypa.io/get-pip.py").read()
        gp = gp.replace(b"sys.exit", b"")
        exec(gp)
    except Exception as e:
        print(e, YELLOW)
        print("Failed to install pip.", RED)
        sys.exit(1)

try:
    import pip  # noqa:F811
except Exception as e:
    print(e, YELLOW)
    print("Failed to install pip.", RED)
    sys.exit(1)

try:
    import virtualenv
except Exception as e:
    print(e, YELLOW)
    print("Installing virtualenv...", GREEN)
    try:
        subprocess.check_call(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "--no-cache-dir",
                    "virtualenv",
                ],
                shell=True if "win32" in sys.platform else False,
            )    
    except Exception as e:
        print(e, YELLOW)
        print("Failed to install virtualenv.", GREEN)
        sys.exit(1)

try:
    import virtualenv  # noqa:F811
except Exception as e:
    print(e, YELLOW)
    print("Failed to install virtualenv.", GREEN)
    sys.exit(1)

if not os.path.isdir("q2rad"):
    print("Creating virtual enviroment...", GREEN)
    virtualenv.cli_run(["q2rad"])
    print("Done.", GREEN)

bin_folder = "Scripts" if "win32" in sys.platform else "bin"
activator = Path(f"q2rad/{bin_folder}/activate_this.py")
start_app_src = Path(f"q2rad/{bin_folder}/{'q2rad.exe' if 'win32' in sys.platform else 'q2rad'}")
start_app_dst = Path(f"./Start q2rad.{'exe' if 'win32' in sys.platform else ''}")

if os.path.isfile(activator):
    exec(open(activator).read(), {"__file__": activator})
    try:
        print("Starting q2rad...", GREEN)
        from q2rad.q2rad import main

        main()
    except Exception as e:
        print(e, YELLOW)
        print_out("Installing q2rad...", GREEN)
        try:
            subprocess.check_call(
                [
                    Path(f"q2rad/{bin_folder}/python"),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "--no-cache-dir",
                    "q2rad",
                ],
                shell=True if "win32" in sys.platform else False,
            )
        except Exception as e:
            print(e)
            print("Failed to install and run q2rad.", RED)
            sys.exit(0)
        print("Starting q2rad...")
        py3bin = os.path.abspath(f"q2rad/{bin_folder}/{os.path.basename(sys.executable)}")
        code_string = '"from q2rad.q2rad import main;main()"'
        if 'win32' not in sys.platform:
            code_string = code_string.replace('"', "")
        os.execv(py3bin, [py3bin, "-c", code_string])

else:
    print("Failed to create virtual enviroment.", RED)
