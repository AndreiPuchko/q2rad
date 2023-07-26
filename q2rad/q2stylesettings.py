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


from q2rad import Q2Form
from q2rad.q2raddb import int_
import logging

_logger = logging.getLogger(__name__)


class AppStyleSettings(Q2Form):
    def __init__(self, title=""):
        super().__init__("Style Settings")

    def on_init(self):
        self.color_modes = {"dark": "Dark", "light": "Light", "clean": "Clean"}
        self.last_font_size = self.q2_app.q2style.font_size
        # print("==", self.last_font_size)
        self.last_color_mode = self.q2_app.q2style.color_mode
        self.add_control(
            "color_mode",
            "Color mode",
            pic="System defaulf;Dark;Light;Clean",
            datatype="char",
            control="radio",
            datalen=10,
            valid=self.style_valid,
            data=self.color_modes.get(
                self.q2_app.q2style.color_mode, self.q2_app.q2style.get_system_color_mode()
            ),
        )

        self.add_control("/h", "Font size")
        self.add_control("minus", "-", datatype="int", control="button", valid=self._font_minus)

        self.add_control(
            "font_size",
            "",
            datalen=6,
            datatype="int",
            control="line",
            data=self.q2_app.q2style.font_size,
            valid=self.font_size_valid,
        )
        self.add_control("plus", "+", datatype="int", control="button", valid=self._font_plus)
        self.add_control("apply", "Apply immediately", control="check", data=True)

        self.add_control("/s")
        self.add_control("/")

        self.ok_button = 1
        self.cancel_button = 1

    def _font_plus(self):
        self.s.font_size = int_(self.s.font_size) + 1
        self.font_size_valid()

    def _font_minus(self):
        self.s.font_size = int_(self.s.font_size) - 1
        self.font_size_valid()

    def get_color_mode(self):
        color_mode = self.s.color_mode.lower()
        if color_mode not in ("dark", "light", "clean"):
            color_mode = None
        return color_mode

    def valid(self):
        self.style_valid()
        color_mode = self.get_color_mode()
        self.q2_app.q2style.font_size = int_(self.s.font_size)
        self.q2_app.settings.set("Style Settings", "color_mode", color_mode)
        self.q2_app.settings.set("Style Settings", "font_size", self.s.font_size)
        self.q2_app.set_color_mode(color_mode)

    def font_size_valid(self):
        if int_(self.s.font_size) < 8:
            self.s.font_size = 8
        if self.s.apply:
            self.q2_app.q2style.font_size = int_(self.s.font_size)
            self.style_valid()

    def style_valid(self):
        self.q2_app.set_color_mode(self.get_color_mode())

    def close(self):
        if not self.ok_pressed:
            self.q2_app.q2style.font_size = self.last_font_size
            self.q2_app.set_color_mode(self.last_color_mode)
        return super().close()
