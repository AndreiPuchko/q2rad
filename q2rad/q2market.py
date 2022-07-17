if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2dialogs import q2AskYN
from q2rad import Q2Form

import gettext

from q2gui.q2app import Q2Actions

_ = gettext.gettext


class Q2Market(Q2Form):
    def __init__(self):
        super().__init__("q2Market")
        self.no_view_action = True

    def on_init(self):
        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
