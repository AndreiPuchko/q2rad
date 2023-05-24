import sys
import os
import urllib.request

try:
    import pip
except:
    print("Installing pip...")
    gp = urllib.request.urlopen("https://bootstrap.pypa.io/get-pip.py").read()
    exec(gp)
try:
    import pip
except:
    print("cant install pip")
    sys.exit(1)
try:
    import virtualenv
except:
    print("Installing virtualenv...")
    pip.main(["install", "--upgrade", "virtualenv"])
try:
    import virtualenv
except:
    print("cant install virtualenv")
    sys.exit(1)
if not os.path.isdir("q2rad"):
    virtualenv.cli_run(["q2rad"])
if os.path.isfile("q2rad/bin/activate_this.py"):
    exec(open("q2rad/bin/activate_this.py").read())
    try_to_install = True
    while True:
        try:
            from q2rad.q2rad import main
            main()
        except:
            if try_to_install:
                pip.main(["install", "--upgrade", "q2rad"])
                try_to_install = False
                continue
        break
