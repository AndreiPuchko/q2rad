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

if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2gui.q2model import Q2Model
from q2gui.q2dialogs import q2AskYN
from q2rad import Q2Form
import json
from q2rad.q2raddb import read_url, open_url

import gettext

from q2rad.q2appmanager import AppManager

_ = gettext.gettext


class Q2Market(Q2Form):
    def __init__(self, title=""):
        super().__init__("q2Market")
        self.no_view_action = True

    def on_init(self):
        self.add_control("app_title", _("Name"), datatype="char", datalen=100)
        self.add_control("app_version", _("Version"), datatype="char", datalen=100)
        self.add_control(
            "app_description", _("Description"), datatype="char", datalen=100
        )
        self.add_control("app_url", _("Path"), datatype="char", datalen=100)

        q2market_catalogue_url = f"{self.q2_app.q2market_url}/q2market.json"
        data = json.loads(read_url(q2market_catalogue_url).decode("utf-8"))
        rez = []
        for x in data:
            rec = data[x]
            rec["app_url"] = x
            rez.append(rec)
        model = Q2Model()
        model.set_records(rez)
        self.set_model(model)
        self.add_action_view()
        self.add_action("Select", self.load_app, tag="select", eof_disabled=1)

    def load_app(self):
        selected_app = self.get_current_record()
        if (
            q2AskYN(
                "Do you really want to download and install this App:"
                + "<p><b>{app_title}</b>".format(**selected_app)
                + "<p><i>{app_description}</i>".format(**selected_app)
            )
            == 2
        ):
            if not selected_app["app_url"].endswith(".json"):
                selected_app["app_url"] += ".json"
            data = json.load(open_url(selected_app["app_url"]))
            AppManager.import_json_app(data)
            # self.q2_app.migrate_db_data()
            self.q2_app.open_selected_app()
        self.close()
