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

from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2rad import Q2Form
from q2gui.q2app import Q2Actions
from q2gui import q2app
import gettext
import base64

_ = gettext.gettext


class Q2Constants(Q2Form):
    def __init__(self, title=""):
        super().__init__("Constants")
        self.no_view_action = True

    def on_init(self):
        self.add_control("const_name", _("Name"), datatype="char", datalen=100, pk="*")
        loader_actions = Q2Actions()
        loader_actions.show_main_button = False
        loader_actions.add_action("Load image", self.load_image)
        loader_actions.add_action("Show as image", self.show_image)
        self.add_control("const_text", _("Label"), datatype="char", datalen=250)
        self.add_control("const_value", _("Value"), datatype="text", actions=loader_actions)
        self.add_control("comment", _("Comment"), datatype="text")

        cursor: Q2Cursor = self.q2_app.db_data.table(table_name="constants")
        model = Q2CursorModel(cursor)
        model.set_order("const_name").refresh()
        self.set_model(model)
        self.add_action("/crud")

    def load_image(self):
        _q2app: q2app = self.q2_app
        image_file = _q2app.get_open_file_dialoq("Open image", filter="Images (*.png *.jpg)")[0]
        self.s.const_value = base64.b64encode(open(image_file, "rb").read()).decode()

    def show_image(self):
        iform = Q2Form("Image viewer")
        iform.add_control("image", control="image", data=self.s.const_value)
        iform.run()


class q2const:
    def __getattr__(self, __name):
        return q2app.q2_app.db_data.get("constants", f"const_name = '{__name}'", "const_value")

    def __setattr__(self, __name, __value):
        const_name = self.get_const_name(__name)
        if const_name:
            q2app.q2_app.db_data.update("constants", {"const_name": __name, "const_value": __value})
        else:
            q2app.q2_app.db_data.insert("constants", {"const_name": __name, "const_value": __value})

    def get_const_name(self, __name):
        const_name = q2app.q2_app.db_data.get("constants", f"const_name = '{__name}'", "const_name")

        return const_name

    def check(self, const_name="", const_text="", const_value="", comment=""):
        if const_name == "":
            return
        _const_name = self.get_const_name(const_name)
        if not _const_name:
            q2app.q2_app.db_data.insert(
                "constants",
                {
                    "const_name": const_name,
                    "const_value": const_value,
                    "const_text": const_text,
                    "comment": comment,
                },
            )
