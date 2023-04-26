if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2rad import Q2Form
from q2rad.q2raddb import int_
import logging

_logger = logging.getLogger(__name__)


class AppStyleSettings(Q2Form):
    def __init__(self, title=""):
        super().__init__("Style Settings")

    def on_init(self):
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
            data=2,
        )

        self.add_control(
            "font_size",
            "Font size",
            datalen=6,
            datatype="int",
            control="spin",
            valid=self.style_valid,
            data=self.q2_app.q2style.font_size,
        )

        self.ok_button = 1
        self.cancel_button = 1

    def after_form_show(self):
        self.s.color_mode = {"dark": "Dark", "light": "Light", "clean": "Clean"}.get(
            self.q2_app.q2style.color_mode, self.q2_app.q2style.get_system_color_mode()
        )

    def get_color_mode(self):
        color_mode = self.s.color_mode.lower()
        if color_mode not in ("dark", "light", "clean"):
            color_mode = None
        return color_mode

    def valid(self):
        color_mode = self.get_color_mode()
        self.q2_app.q2style.font_size = int_(self.s.font_size)
        self.q2_app.settings.set("Style Settings", "color_mode", color_mode)
        self.q2_app.settings.set("Style Settings", "font_size", self.s.font_size)
        self.q2_app.set_color_mode(color_mode)

    def style_valid(self):
        self.q2_app.q2style.font_size = int_(self.s.font_size)
        self.q2_app.set_color_mode(self.get_color_mode())
        self.q2_app.set_color_mode(self.get_color_mode())

    def close(self):
        if not self.ok_pressed:
            self.q2_app.q2style.font_size = self.last_font_size
            self.q2_app.set_color_mode(self.last_color_mode)
        return super().close()
