import sys
import os
import urllib.request
import subprocess

if not os.path.isdir("q2rad"):
    os.mkdir("q2rad")
os.chdir("q2rad")

try:
    import pip
except Exception as e:
    print(e)
    print("Installing pip...")
    gp = urllib.request.urlopen("https://bootstrap.pypa.io/get-pip.py").read()
    exec(gp)

try:
    import pip  # noqa:F811
except Exception as e:
    print(e)
    print("Failed to install pip")
    sys.exit(1)

try:
    import virtualenv
except Exception as e:
    print(e)
    print("Installing virtualenv...")
    pip.main(["install", "--upgrade", "virtualenv"])
    # sys.argv = ["pip", "install", "--upgrade", "virtualenv"]
    # runpy.run_module("pip", run_name="__main__")

try:
    import virtualenv  # noqa:F811
except Exception as e:
    print(e)
    print("Failed to install virtualenv")
    sys.exit(1)

if not os.path.isdir("q2rad"):
    print("Creating virtual enviroment")
    virtualenv.cli_run(["q2rad"])

activator = "q2rad/bin/activate_this.py"
if os.path.isfile(activator):
    exec(open(activator).read(), {"__file__": activator})
    try:
        print("Starting q2rad")
        from q2rad.q2rad import main

        main()
    except Exception as e:
        print(e)
        subprocess.check_call(
            [
                "q2rad/bin/python",
                "-m",
                "pip",
                "install",
                "--upgrade",
                "--no-cache-dir",
                "q2rad",
            ],
            shell=True if "win32" in sys.platform else False,
        )
        py3bin = os.path.abspath(f"q2rad/bin/{os.path.basename(sys.executable)}")
        os.execv(py3bin, [py3bin, "-c", "from q2rad.q2rad import main;main()"])
else:
    print("Failed to create virtual enviroment")
