from importlib.util import spec_from_file_location, module_from_spec
from pathlib import Path


def run_local_hook(_hook_file="_q2rad.py"):
    hook = Path.cwd() / _hook_file
    if not hook.is_file():
        return

    spec = spec_from_file_location("_q2_hook", hook)
    mod = module_from_spec(spec)
    spec.loader.exec_module(mod)


run_local_hook("_q2rad.py")

from q2rad.version import __version__
from q2gui.q2app import Q2App
from q2gui.q2form import Q2Form


from q2gui.q2app import load_q2engine

load_q2engine(globals(), "PyQt6")
