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
from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2dialogs import q2Mess, q2AskYN, q2working

from q2rad.q2utils import Q2Form
from q2gui import q2app
from q2rad.q2appmanager import AppManager
import gettext
import json


_ = gettext.gettext


class Q2Extensions(Q2Form):
    def __init__(self, title=""):
        super().__init__("Extensions")
        self.no_view_action = True

    def on_init(self):
        self.db = q2app.q2_app.db_data
        self.add_control("prefix", _("Name"), datatype="char", datalen=50, pk="*")
        self.add_control("seq", _("Sequence number"), datatype="int")
        self.add_control("datetime", _("Uploaded"), datatype="char", datalen=16, readonly=True)
        self.add_control("checkupdates", _("Check for updatea"), control="check", datatype="char", datalen=1)
        self.add_control("comment", _("Comment"), datatype="text")

        cursor: Q2Cursor = self.q2_app.db_data.table(table_name="extensions")
        model = Q2CursorModel(cursor)
        model.set_order("seq").refresh()
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("Export|as JSON file", self.export_json, eof_disabled=True)
        self.add_action("Export|to q2Market", self.export_q2market, eof_disabled=True)
        self.add_action("Import|from JSON file", self.import_json, eof_disabled=True)
        self.add_action("Import|from q2Market", self.import_q2market, eof_disabled=True)

    def info(self):
        pass

    def export_json(self, file):
        prefix = self.r.prefix
        filetype = "JSON(*.json)"
        if not file:
            desktop = os.path.expanduser("~/Desktop")
            file = f"{desktop}/{prefix}.json"
            file, filetype = q2app.q2_app.get_save_file_dialoq(
                f"Export Extension ({prefix})", filter=filetype, path=file
            )
        if not file:
            return
        file = self.validate_impexp_file_name(file, filetype)
        if file:

            def get_ext_json(prefix=prefix):
                return AppManager._get_app_json(prefix)

            ext_json = q2working(get_ext_json, "Prepare data...")
            if ext_json:
                json.dump(ext_json, open(file, "w"), indent=1)

    def export_q2market(self):
        pass

    def import_json(self, file=""):
        prefix = self.r.prefix
        filetype = "JSON(*.json)"
        if not file:
            file, filetype = q2app.q2_app.get_open_file_dialoq(
                f"Import Extension ({prefix})", filter=filetype
            )

        if not file or not os.path.isfile(file):
            return

        data = json.load(open(file))
        if data:
            AppManager.import_json_app(data, prefix=prefix)
            self.q2_app.open_selected_app()

    def import_q2market(self):
        pass
