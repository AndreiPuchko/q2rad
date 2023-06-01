import sys
import os
import urllib.request
import subprocess
from pathlib import Path
import pkgutil
import stat


RED = chr(27) + "[38;5;1m"
GREEN = chr(27) + "[38;5;2m"
YELLOW = chr(27) + "[38;5;3m"
RESET = chr(27) + "[0;0m"
CLEAR = chr(27) + "[2J"


if os.path.isfile("_tmp.py"):
    os.remove("_tmp.py")


print_ = print


def print_out(text="", color=None, RESET=RESET, print_=print_):
    print_(f'{"" if color is None else color}{text}', end="")
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
    import pip  # noqa:F401
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
        print("Installing q2rad...", GREEN)
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
                stdout=sys.stdout,
            )
        except Exception as e:
            print(e)
            print("Failed to install and run q2rad.", RED)
            sys.exit(0)
        print("Starting q2rad...", GREEN)
        py3bin = os.path.abspath(f"q2rad/{bin_folder}/python")
        code_string = "from q2rad.q2rad import main;main()"

        if "win32" in sys.platform:
            script_ext = "bat"
            start_prefix = ""
            shebang = ""
        elif "darwin" in sys.platform:
            script_ext = "command"
            start_prefix = "nohup "
            shebang = "#!/bin/bash"
        else:
            script_ext = "sh"
            start_prefix = "nohup "
            shebang = "#!/bin/bash"
        try:
            start_script = (
                f"{shebang}\n"
                f'cd "{os.path.abspath(".")}"\n'
                f"{start_prefix}"
                f'"{py3bin}"'
                f' -c "{code_string}"'
            )
            open(f"../start-q2rad.{script_ext}", "w").write(start_script)
        except Exception as e:
            print(f"Failed to create start shell script: {e}", RED)
            print(start_script)

        try:
            if "win32" not in sys.platform:
                st = os.stat(f"../start-q2rad.{script_ext}")
                os.chmod(f"../start-q2rad.{script_ext}", st.st_mode | stat.S_IEXEC)
                os.execv(py3bin, [py3bin, "-c", code_string])
            else:
                subprocess.Popen(
                    ["powershell", f'&"{py3bin}"', "-c", f'"{code_string}"'], start_new_session=True
                )
        except Exception as e:
            print(f"Failed to start: {e}", RED)
else:
    print("Failed to create virtual enviroment.", RED)
