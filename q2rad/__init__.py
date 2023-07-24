from q2rad.version import __version__
from q2gui.q2app import Q2App
from q2gui.q2form import Q2Form


from q2gui.q2app import load_q2engine

load_q2engine(globals(), "PyQt6")


from q2rad.q2utils import grid_print

Q2Form.grid_print = grid_print
