if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2gui.q2dialogs import q2AskYN
from q2gui.q2widget import Q2Widget

from q2gui.q2app import Q2Actions
from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel
from q2gui.q2utils import dotdict, set_dict_default, num, int_
from q2report.q2report import Q2Report
from q2rad.q2queries import re_find_param
from q2rad.q2queries import Q2QueryEdit
from q2rad.q2raddb import q2cursor
from q2gui import q2app
from q2gui.q2dialogs import q2WaitShow, q2Wait, q2WaitMax, q2WaitStep
import json
import os
import gettext

from q2rad import Q2Form

_ = gettext.gettext


class Q2RadReport(Q2Report):
    def __init__(self, content=""):
        super().__init__()
        self.load(content)
        self.data["const"] = q2app.q2_app.const
        self.waitbar = None
        self.data_sources_lenght = {}

    def prepare_output_file(self, output_file):
        rez_name = ""
        if "." not in output_file:
            rez_name = f"tmp/repo.{output_file}"
        else:
            form = Q2Form("Report to")
            form.heap.mode = ""

            def repo_valid(mode):
                form.heap.mode = mode
                form.close()

            form.add_control("/h")
            form.add_control("/s")
            form.add_control("/v")
            form.add_control(
                "html",
                "HTML",
                control="button",
                datalen=10,
                valid=lambda: repo_valid("html"),
                eat_enter=1,
            )
            form.add_control(
                "docx",
                "DOCX",
                control="button",
                datalen=10,
                valid=lambda: repo_valid("docx"),
                eat_enter=1,
            )
            form.add_control(
                "docx",
                "XLSX",
                control="button",
                datalen=10,
                valid=lambda: repo_valid("xlsx"),
                eat_enter=1,
            )
            form.add_control("/")
            form.add_control("/s")
            form.add_control("/")
            form.cancel_button = 1
            form.do_not_save_geometry = 1
            form.run()
            if form.heap.mode:
                rez_name = f"tmp/repo.{form.heap.mode}"
            else:
                rez_name = ""
        if rez_name:
            if not os.path.isdir(os.path.dirname(rez_name)):
                os.mkdir(os.path.dirname(rez_name))
            co = 0
            name, ext = os.path.splitext(rez_name)
            while True:
                lockfile = (
                    f"{os.path.dirname(rez_name)}/.~lock.{os.path.basename(rez_name)}#"
                )
                if os.path.isfile(lockfile):
                    co += 1
                    rez_name = f"{name}{co:03d}{ext}"
                else:
                    break
        return rez_name

    def data_start(self):
        super().data_start()
        self.waitbar = q2WaitShow(self.data_cursors[self.current_data_set_name].row_count())

    def data_step(self):
        super().data_step()
        self.waitbar.step()

    def data_stop(self):
        super().data_stop()
        self.waitbar.close()

    def run(self, output_file="tmp/repo.html"):
        output_file = self.prepare_output_file(output_file)
        if not output_file:
            return
        self.data_cursors = {}

        data = {}
        # w = q2WaitShow("Open queries:", len(self.report_content["queries"]))
        # for x in self.report_content["queries"]:
        #     w.step(x)
        #     sql = self.report_content["queries"][x]
        #     sql_params = re_find_param.findall(sql)
        #     for p in sql_params:
        #         value = self.params.get(p[1:], "")
        #         sql = sql.replace(p, f"'{value}'")
        #         data[x] = q2cursor(sql).records()
        # w.close()

        def worker():
            def real_worker():
                q2WaitMax(len(self.report_content["queries"]))
                for x in self.report_content["queries"]:
                    q2WaitStep()
                    sql = self.report_content["queries"][x]
                    sql_params = re_find_param.findall(sql)
                    for p in sql_params:
                        value = self.params.get(p[1:], "")
                        sql = sql.replace(p, f"'{value}'")
                        self.data_cursors[x] = q2cursor(sql)
                        data[x] = self.data_cursors[x].records()
                        # print(q2app.q2_app.db_data.last_sql_error)
            return real_worker

        q2Wait(worker(), "W o r k i n g")

        super().run(output_file, data=data)


class Q2Reports(Q2Form):
    def __init__(self):
        super().__init__("Reports")
        self.no_view_action = True

    def on_init(self):
        self.report_edit_form = None

        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("/")

        self.add_control("anchor", "**", control="label")

        self.add_control(
            "content",
            "",
            datatype="bigtext",
            control="codejson",
            nogrid=0,
            noform=1,
        )
        self.add_control("comment", _("Comment"), datatype="text", noform=1)

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="reports")
        model = Q2CursorModel(cursor)
        model.set_order("name").refresh()
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("Run", self.run_report, hotkey="F4")
        self.add_action("-")
        self.add_action("JSON", self.edit_json)

    def run_report(self):
        rep = Q2RadReport(self.r.content)
        rep.run()

    def edit_json(self):
        form = Q2Form("Edit report JSON")
        json_editor_actions = Q2Actions()

        def save_json():
            json_file_name = form.q2_app.get_save_file_dialoq(filter="JSON(*.json)")[0]
            if json_file_name:
                json_file_name = form.validate_impexp_file_name(json_file_name, "json")
                open(json_file_name, "w", encoding="utf8").write(form.s.json)

        json_editor_actions.add_action("Save as", save_json, hotkey="")
        form.add_control("/v")
        form.add_control(
            "json",
            control="code_json",
            data=self.r.content,
            actions=json_editor_actions,
        )
        form.ok_button = 1
        form.cancel_button = 1
        form.run()
        if form.ok_pressed:
            self.model.update({"name": self.r.name, "content": form.s.json})
            self.set_grid_index(self.current_row)

    def after_form_show(self):
        self.anchor: Q2Widget = self.w.anchor
        if self.anchor is not None:
            self.anchor.set_visible(False)

            self.report_edit_form = Q2ReportEdit()
            w = self.report_edit_form.get_widget()
            self.widgets()["report_report"] = w
            self.report_edit_form.form_stack = [w]
            self.anchor.add_widget_below(w)
            w.show()
            self.report_edit_form.widget().restore_grid_columns()

        if self.crud_mode == "NEW":
            self.report_edit_form.set_content("")
        else:
            self.report_edit_form.set_content(self.r.content)

    def before_crud_save(self):
        self.s.content = self.report_edit_form.get_content()


class ReportForm:
    def move_up(self):
        if self.widget().get_layout_position() == 1:
            return
        self.widget().move_up()

    def move_down(self):
        self.widget().move_down()

    def remove_me(self, text=""):
        if self.widget().get_layout_count() > 2:
            if q2AskYN(_(f"Remove {text}?")) == 2:
                self.widget().remove()
                return True

    def hide_show(self):
        first_widget_state = None
        for x in self.anchor.get_layout_widgets()[1:]:
            if first_widget_state is None:
                first_widget_state = x.is_visible()
            x.set_visible(not first_widget_state)

    def set_style_button(self, text=""):
        self.w.style_button.hide_column_headers()
        self.w.style_button.hide_row_headers()
        self.w.style_button.set_auto_expand()
        self.w.style_button.set_row_count(1)
        self.w.style_button.set_column_count(1)
        self.w.style_button.set_cell_style_sheet(
            self.report_report_form.style_cell_style
        )
        self.set_style_button_text(text)

    def set_style_button_text(self, text):
        self.w.style_button.set_cell_text(text)


class Q2ReportEdit(Q2Form):
    def __init__(self):
        super().__init__("Report Edit")

    def on_init(self):
        self.query_edit = Q2QueryEdit()
        self.layout_edit = Q2ReportReport(self)
        self.add_control("/t", "Layout")
        self.add_control("rl", "", widget=self.layout_edit, nogrid=1, migrate=0)
        self.add_control("/t", "Query")
        self.add_control("ql", "", widget=self.query_edit, nogrid=1, migrate=0)
        self.add_control("/t", "Setup")
        self.add_control("before_script", "", control="code")
        self.add_control("/t", "Module")
        self.add_control("module", "", control="code")
        self.add_control("/t", "Comment")
        self.add_control("comment", _("Comment"), datatype="text")

    def set_content(self, content):
        if content == "":
            content = "{}"
        if isinstance(content, str):
            content_json = json.loads(content)
        else:
            content_json = content
        self.query_edit.set_content(content_json)
        self.layout_edit.set_content(content_json)

    def get_content(self, str_mode=True):
        content = self.query_edit.get_content(str_mode=False)
        content.update(self.layout_edit.get_content(str_mode=False))
        if str_mode:
            return json.dumps(content, indent=2)
        else:
            return content


class Q2ReportReport(Q2Form):
    def __init__(self, report_edit_form_form):
        super().__init__("Report Layout")
        self.i_am_child = True
        self.report_edit_form = report_edit_form_form
        self.anchor = None
        self.ratio = 45
        self.report_report_form = self
        self.current_propertys = {}
        self.lock_status_bar = True

        self.report_data = dotdict()

        self.set_default_report_content()

        self.sizes_cell_style = """
                background:lightsteelblue;
                text-align:center;
                vertical-align:middle;
                border-style:solid;
                border-radius:0;
                """

        self.style_cell_style = """
                background:LightCyan;
                text-align:center;
                vertical-align:middle;
                border-style:solid;
                border-radius:0;
                """

        self.current_focus = None
        # self.current_style = ""

        if 1:  # Actions
            actions = Q2Actions()
            actions.add_action("HTML", lambda: self.run_report("html"))
            actions.add_action("DOCX", lambda: self.run_report("docx"))
            actions.add_action("XLSX", lambda: self.run_report("xlsx"))
            actions.show_main_button = 0

        if self.add_control("/h"):
            if self.add_control("/v"):
                self.add_control("/h")
                self.add_control(
                    "style_button",
                    control="sheet",
                    when=self.style_button_pressed,
                    valid=self.style_button_pressed,
                    dblclick=self.style_button_pressed,
                )

                self.add_control("", control="label", tag="pages", actions=actions)
                self.add_control("/")
                if self.add_control("/vr", tag="pages"):
                    self.add_control("anchor", "*", control="label")
                    self.add_control("/")
                self.add_control("/")
        if self.add_control("/v", tag="style_panel"):
            self.add_control("/vr")
            self.add_control("/f", "Font")
            self.add_control(
                "font_family",
                "Font family",
                control="combo",
                pic="Arial;Times;Courier",
                check=1,
                valid=self.prop_font_family,
                when=self.prop_font_family,
            )
            self.add_control(
                "font_size",
                "Font size",
                control="spin",
                datalen=5,
                datatype="int",
                check=1,
                valid=self.prop_font_size,
                when=self.prop_font_size,
            )
            self.add_control(
                "font_weight",
                "Font weight",
                control="check",
                check=1,
                valid=self.prop_font_weight,
                when=self.prop_font_weight,
            )
            self.add_control("/")

            self.add_control(
                "/h",
                "Borders",
                check=1,
                tag="border_width",
                valid=self.prop_border,
                when=self.prop_border,
            )
            self.add_control(
                "border_left",
                "",
                control="spin",
                datalen=5,
                valid=self.prop_border,
                when=self.prop_border,
            )
            self.add_control("/v")
            self.add_control(
                "border_top",
                "",
                control="spin",
                datalen=5,
                valid=self.prop_border,
                when=self.prop_border,
            )
            self.add_control(
                "border_bottom",
                "",
                control="spin",
                datalen=5,
                valid=self.prop_border,
                when=self.prop_border,
            )
            self.add_control("/")
            self.add_control(
                "border_right",
                "",
                control="spin",
                datalen=5,
                valid=self.prop_border,
                when=self.prop_border,
            )
            self.add_control("/")

            self.add_control(
                "/h",
                "Paddings",
                check=1,
                tag="padding",
                valid=self.prop_padding,
                when=self.prop_padding,
            )
            self.add_control(
                "padding_left",
                "",
                control="doublespin",
                datalen=5,
                datadec=2,
                valid=self.prop_padding,
                when=self.prop_padding,
            )
            self.add_control("/v")
            self.add_control(
                "padding_top",
                "",
                control="doublespin",
                datalen=5,
                datadec=2,
                valid=self.prop_padding,
                when=self.prop_padding,
            )
            self.add_control(
                "padding_bottom",
                "",
                control="doublespin",
                datalen=5,
                datadec=2,
                valid=self.prop_padding,
                when=self.prop_padding,
            )
            self.add_control("/")
            self.add_control(
                "padding_right",
                "",
                control="doublespin",
                datalen=5,
                datadec=2,
                valid=self.prop_padding,
                when=self.prop_padding,
            )
            self.add_control("/")
            if self.add_control("/v", "-"):  # Alignments
                self.add_control(
                    "text_align",
                    _("Horizontal alignment"),
                    control="radio",
                    pic="left;center;right;justify",
                    check="*",
                    valid=self.prop_text_align,
                    when=self.prop_text_align,
                )
                self.add_control(
                    "vertical_align",
                    _("Vertical alignment"),
                    control="radiov",
                    pic="top;middle;bottom",
                    check="*",
                    valid=self.prop_vertical_align,
                    when=self.prop_vertical_align,
                )
                self.add_control("/")

        self.set_content()

    def run_report(self, output_file="html"):
        rep = Q2RadReport(self.report_edit_form.get_content())
        rep.run(output_file)

    def set_default_report_content(self):
        set_dict_default(self.report_data, "pages", [{}])
        set_dict_default(self.report_data, "style", {})

        set_dict_default(self.report_data.style, "font-family", "Arial")
        set_dict_default(self.report_data.style, "font-size", "8pt")
        set_dict_default(self.report_data.style, "font-weight", "normal")

        set_dict_default(self.report_data.style, "border-width", "0 0 0 0")
        set_dict_default(
            self.report_data.style, "padding", "0.05cm 0.05cm 0.05cm 0.05cm"
        )

        # set_dict_default(self.report_data.style, "background-color", "white")
        # set_dict_default(self.report_data.style, "color", "black")

        set_dict_default(self.report_data.style, "text-align", "left")
        set_dict_default(self.report_data.style, "vertical-align", "top")

    def prop_font_size(self):
        self.property_changed("font_size", f"{self.s.font_size}pt")

    def prop_font_family(self):
        self.property_changed("font_family", f"{self.s.font_family}")

    def prop_font_weight(self):
        self.property_changed(
            "font_weight", f"{'bold' if self.s.font_weight else 'normal'}"
        )

    def prop_border(self):
        self.property_changed(
            "border_width",
            " ".join(
                [
                    self.s.border_top,
                    self.s.border_right,
                    self.s.border_bottom,
                    self.s.border_left,
                ]
            ),
        )

    def prop_padding(self):
        self.property_changed(
            "padding",
            " ".join(
                [
                    f"{self.s.padding_top}cm",
                    f"{self.s.padding_right}cm",
                    f"{self.s.padding_bottom}cm",
                    f"{self.s.padding_left}cm",
                ]
            ),
        )

    def prop_text_align(self):
        self.property_changed("text_align", f"{self.s.text_align}")

    def prop_vertical_align(self):
        self.property_changed("vertical_align", f"{self.s.vertical_align}")

    def property_changed(self, prop_name, prop_value):
        if self.lock_status_bar:
            return
        if self.current_propertys is None:
            return

        prop_key = prop_name.replace("_", "-")

        if not self.w.__getattr__(prop_name).check.is_checked():
            del self.current_propertys[prop_key]
        else:
            self.current_propertys[prop_key] = prop_value
        self.style_changed()

    def style_changed(self):
        if self.lock_status_bar:
            return
        if self.current_focus:
            self.current_focus.meta["form"].apply_style()

    def apply_style(self):
        for page in self.get_pages():
            for row_sheet in page.q2_form.get_rows_form_list():
                row_sheet.apply_style()

    def get_pages(self):
        return self.anchor.get_layout_widgets()[1:]

    def style_button_pressed(self):
        self.focus_changed(self.w.style_button)

        self.report_report_form.update_style_bar(
            self.get_style(), self.report_data.style
        )

    def focus_changed(self, widget):
        """for every style-holding widget"""
        if self.current_focus == widget:
            return
        if self.current_focus:
            self.current_focus.clear_selection()
        self.current_focus = widget

    def make_4(self, value):
        value_list = value.split(" ")
        if len(value_list) == 1:
            value_list *= 4
        elif len(value_list) == 2:
            value_list += value_list
        elif len(value_list) == 3:
            value_list.append(value_list[2])
        return value_list

    def update_style_bar(self, parent_style, selected_style):
        if selected_style is None:
            return
        if self.current_focus is None:
            return
        self.lock_status_bar = True
        self.current_propertys = selected_style
        for x in parent_style:
            w = self.widgets().get(x.replace("-", "_"))
            if w:
                w.check.set_enabled(self.current_focus.meta["form"] != self)
                w.check.set_text("")
                if x == "font-weight":
                    w.set_text("*" if parent_style[x] == "bold" else "")
                elif x == "border-width":
                    style_value = self.make_4(parent_style[x])
                    self.s.border_top = style_value[0]
                    self.s.border_right = style_value[1]
                    self.s.border_bottom = style_value[2]
                    self.s.border_left = style_value[3]
                elif x == "padding":
                    style_value = self.make_4(parent_style[x].replace("cm", ""))
                    self.s.padding_top = style_value[0]
                    self.s.padding_right = style_value[1]
                    self.s.padding_bottom = style_value[2]
                    self.s.padding_left = style_value[3]
                elif x == "text-align":
                    self.s.text_align = parent_style[x]
                elif x == "vertical-align":
                    self.s.vertical_align = parent_style[x]
                elif x == "font-size":
                    w.set_text(parent_style[x].replace("pt", ""))
                else:
                    w.set_text(parent_style[x])

        for x in selected_style:
            w = self.widgets().get(x.replace("-", "_"))
            if w:
                w.check.set_text(True)
        self.lock_status_bar = False

    def set_style_button_text(self, text):
        ReportForm.set_style_button_text(self, text)

    def get_style(self):
        style = {}
        style.update(self.report_data.get("style", {}))
        return style

    def set_content(self, content_json={}):
        self.report_data.style.update(content_json.get("style", {}))
        self.report_data.pages = content_json.get("pages", [])[:]
        self.set_default_report_content()
        if self.report_data is not None:
            self.show_content()

    def get_content(self, str_mode=True):
        content = {}
        pages = []
        if self.anchor is not None:
            # for x in self.anchor.get_layout_widgets()[1:]:
            for x in self.get_pages():
                pages.append(x.q2_form.get_content())
        content["pages"] = pages
        content["style"] = self.report_data.get("style", {})
        if str_mode:
            return json.dumps(content, indent=2)
        else:
            return content

    def after_form_show(self):
        self.w.style_panel.set_size_policy("maximum", "preffered")
        self.w.font_weight.set_title("Bold")
        ReportForm.set_style_button(self, "Report")
        self.w.style_button.set_focus()

    def show_content(self):
        if self.widget() is None:
            return
        self.anchor: Q2Widget = self.w.anchor
        if self.anchor is not None:
            self.anchor.set_visible(False)
            for page in self.report_data["pages"]:
                self.anchor.add_widget_below(Q2ReportPage(self, page).get_widget(), -1)


class Q2ReportPage(Q2Form, ReportForm):
    def __init__(self, report_report_form, page_data={}):
        super().__init__("Report Page")
        self.i_am_child = True
        self.report_report_form: Q2ReportReport = report_report_form

        self.anchor = None
        self.page_data = dotdict(page_data)

        set_dict_default(self.page_data, "columns", [{}])
        set_dict_default(self.page_data, "style", {})

        set_dict_default(self.page_data, "page_width", 21.0)
        set_dict_default(self.page_data, "page_height", 29.0)
        set_dict_default(self.page_data, "page_margin_left", 2.0)
        set_dict_default(self.page_data, "page_margin_top", 2.0)
        set_dict_default(self.page_data, "page_margin_right", 1.0)
        set_dict_default(self.page_data, "page_margin_bottom", 2.0)

        actions = Q2Actions()
        actions.add_action("Clone", self.clone)
        actions.add_action("Add above", self.add_above)
        actions.add_action("Add below", self.add_below)
        actions.add_action("-")
        actions.add_action("Hide/Show", self.hide_show)
        actions.add_action("Remove", self.remove_me)
        actions.add_action("Move up", self.move_up)
        actions.add_action("Move down", self.move_down)
        actions.show_actions = 0
        actions.show_main_button = 0

        self.add_control("/v", "-")
        self.add_control("/h")
        self.add_control(
            "style_button",
            control="sheet",
            when=self.style_button_pressed,
            valid=self.style_button_pressed,
            dblclick=self.style_button_pressed,
        )

        self.add_control("page_toolbar", actions=actions, control="toolbar")
        self.add_control(
            "width",
            _("Width"),
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.page_data.page_width,
            valid=self.page_size_changed,
        )
        self.add_control(
            "height",
            _("Height"),
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.page_data.page_height,
            valid=self.page_size_changed,
        )
        self.add_control(
            "left",
            _("Left"),
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.page_data.page_margin_left,
            valid=self.page_size_changed,
        )
        self.add_control(
            "right",
            _("Right"),
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.page_data.page_margin_right,
            valid=self.page_size_changed,
        )
        self.add_control(
            "top",
            _("Top"),
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.page_data.page_margin_top,
            valid=self.page_size_changed,
        )
        self.add_control(
            "bottom",
            _("Bottom"),
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.page_data.page_margin_bottom,
            valid=self.page_size_changed,
        )
        self.add_control("/s")
        self.add_control("/")
        self.add_control("/v", "-")
        self.add_control("anchor", "**", control="label")

    def page_size_changed(self):
        self.page_data.page_width = self.s.width
        self.page_data.page_height = self.s.height
        self.page_data.page_margin_top = self.s.top
        self.page_data.page_margin_bottom = self.s.bottom
        self.page_data.page_margin_left = self.s.left
        self.page_data.page_margin_right = self.s.right
        self._repaint()

    def style_button_pressed(self):
        self.report_report_form.focus_changed(self.w.style_button)
        self.report_report_form.update_style_bar(self.get_style(), self.page_data.style)

    def clone(self):
        self.widget().add_widget_below(
            Q2ReportPage(self.report_report_form, self.get_content()).get_widget()
        )

    def add_below(self):
        self.widget().add_widget_below(
            Q2ReportPage(self.report_report_form, {}).get_widget()
        )

    def add_above(self):
        self.widget().add_widget_above(
            Q2ReportPage(self.report_report_form, {}).get_widget()
        )

    def remove_me(self):
        return super().remove_me("page")

    def get_pixel_page_width(self):
        return num(self.report_report_form.ratio * self.get_cm_page_width())

    def get_cm_page_width(self):
        return num(
            (
                num(self.page_data.page_width)
                - num(self.page_data.page_margin_left)
                - num(self.page_data.page_margin_right)
            )
        )

    def get_style(self):
        style = self.report_report_form.get_style()
        style.update(self.page_data.get("style", {}))
        return style

    def after_form_show(self):
        self.set_content()
        ReportForm.set_style_button(self, "Page")

    def set_content(self):
        self.anchor: Q2Widget = self.w.anchor
        if self.anchor is not None:
            self.anchor.set_visible(False)
            for columns in self.page_data["columns"]:
                self.anchor.add_widget_below(
                    Q2ReportColumns(self, columns).get_widget(), -1
                )

    def get_rows_form_list(self):
        rez = []
        for x in self.get_columns():
            # rez.extend(x.q2_form.get_rows_form_list())
            rez.extend(x.get_rows_form_list())
        return rez

    def get_content(self):
        columns = []
        if self.anchor is not None:
            for x in self.get_columns():
                # columns.append(x.q2_form.get_content())
                columns.append(x.get_content())
        self.page_data["columns"] = columns
        if self.page_data.style == {}:
            del self.page_data.style

        return self.page_data

    def get_columns(self):
        if self.anchor is None:
            return []
        return [x.q2_form for x in self.anchor.get_layout_widgets()[1:]]

    def apply_style(self):
        for column in self.get_columns():
            column.apply_style()

    def _repaint(self):
        for x in self.get_columns():
            # x.q2_form._repaint()
            x._repaint()


class Q2ReportColumns(Q2Form, ReportForm):
    def __init__(self, report_page_form: Q2ReportPage, columns_data={}):
        super().__init__("Columns")
        self.i_am_child = True
        self.anchor = None
        self.report_page_form = report_page_form
        self.report_report_form: Q2ReportReport = report_page_form.report_report_form
        self.columns_data = dotdict(columns_data)
        self.columns_sheet = None

        set_dict_default(self.columns_data, "rows", [{}])
        set_dict_default(self.columns_data, "style", {})
        set_dict_default(self.columns_data, "widths", ["50%", "2", "0"])

        self._pixel_columns_widths = []

        self.col_actions = Q2Actions()
        self.section_actions = Q2Actions()

        self.col_actions.add_action("Width", self.cell_double_clicked)
        self.actions.add_action("-")
        self.col_actions.add_action("Add left", self.column_add_left)
        self.col_actions.add_action("Add right", self.column_add_right)
        self.col_actions.add_action("-")
        self.col_actions.add_action("Move left", self.column_move_left)
        self.col_actions.add_action("Move right", self.column_move_right)
        self.col_actions.add_action("-")
        self.col_actions.add_action("Remove", self.column_remove)
        self.col_actions.show_actions = 0
        self.col_actions.show_main_button = 0

        self.section_actions.add_action("Clone", self.clone)
        self.section_actions.add_action("Add above", self.add_above)
        self.section_actions.add_action("Add below", self.add_below)
        self.section_actions.add_action("-")
        self.section_actions.add_action("Hide/Show", self.hide_show)
        self.section_actions.add_action("Remove", self.remove_me)
        self.section_actions.add_action("Move up", self.move_up)
        self.section_actions.add_action("Move down", self.move_down)
        self.section_actions.show_actions = 0
        self.section_actions.show_main_button = 0

        self.add_control("/v", "-")
        self.add_control("/h")
        self.add_control(
            "style_button",
            control="sheet",
            when=self.style_button_pressed,
            valid=self.style_button_pressed,
            actions=self.section_actions,
            eat_enter=1,
        )
        self.add_control(
            "columns_sheet",
            control="sheet",
            actions=self.col_actions,
            valid=self.column_sheet_focus_changed,
            when=self.column_sheet_focus_changed,
            dblclick=self.cell_double_clicked,
            eat_enter=1,
        )
        self.add_control("/")
        self.add_control("/v")
        self.add_control("anchor", "*", control="label")
        self.add_control("/")

    def column_remove(self):
        selected_columns = list(set([x[1] for x in self.columns_sheet.get_selection()]))
        selected_columns.reverse()
        for current_column in selected_columns:
            if not self.can_i_touch_this_column(current_column):
                continue
            self.columns_data.widths.pop(current_column)
            self.columns_sheet.remove_column(current_column)
            for x in self.get_rows_form_list():
                x.column_remove(current_column)
        self._repaint()

    def column_move(self, current_column):
        if current_column >= self.get_column_count() - 1 or current_column < 0:
            return
        tmph = self.columns_data.widths[current_column]
        self.columns_data.widths[current_column] = self.columns_data.widths[
            current_column + 1
        ]
        self.columns_data.widths[current_column + 1] = tmph

        self.columns_sheet.move_column(current_column)
        for x in self.get_rows_form_list():
            x.column_move(current_column)

        self._repaint()

    def column_move_left(self):
        self.column_move(self.columns_sheet.current_column() - 1)

    def column_move_right(self):
        self.column_move(self.columns_sheet.current_column())

    def column_add(self, current_column=None):
        self.columns_sheet.insert_column(current_column)
        self.columns_data.widths.insert(current_column, "0")
        for x in self.get_rows_form_list():
            x.column_insert(current_column)
        self._repaint()

    def column_add_left(self):
        self.column_add(self.columns_sheet.current_column())

    def column_add_right(self):
        self.column_add(self.columns_sheet.current_column() + 1)

    def cell_double_clicked(self):
        self.edit_column_width()

    def get_dec_width(self, width):
        return num(width.replace("%", ""))

    def can_i_touch_this_column(self, column=None):
        if column is None:
            column = self.columns_sheet.current_column()
        width = self.get_dec_width(self.columns_sheet.get_cell_text(0, column))
        if width != 0:
            return True
        else:
            return (
                len(
                    [
                        x
                        for x in self.columns_sheet.get_cell_text()
                        if self.get_dec_width(x) == 0
                    ]
                )
                > 1
            )

    def edit_column_width(self):
        width = self.columns_sheet.get_text()
        if not self.can_i_touch_this_column():
            # only 1 column has free width - can not change it
            return

        form = Q2Form(_("Enter column width"))
        form.do_not_save_geometry = 1
        form.add_control("/h")
        form.add_control(
            "w",
            _("Col width"),
            control="line",
            datatype="dec",
            datalen=5,
            datadec=2,
            data=self.get_dec_width(width),
        )
        form.add_control(
            "p",
            "%",
            datatype="char",
            control="check",
            data="*" if "%" in width else "",
        )
        form.add_control("/s")
        form.ok_button = 1
        form.cancel_button = 1
        form.run()
        if form.ok_pressed:
            self.columns_data.widths[
                self.columns_sheet.current_column()
            ] = f"{form.s.w}{'%' if form.s.p == '*' else ''}"
            self._repaint()

    def style_button_pressed(self):
        self.report_report_form.focus_changed(self.w.style_button)
        self.report_report_form.update_style_bar(
            self.get_style(), self.columns_data.style
        )

    def column_sheet_focus_changed(self):
        # self.report_report_form.focus_changed(self.columns_sheet.get_current_widget())
        self.report_report_form.focus_changed(self.columns_sheet)

    def get_column_count(self):
        return len(self.columns_data.widths)

    def remove_me(self):
        return super().remove_me("columns")

    def recalc_columns_pixel_width(self):
        _columns_count = self.get_column_count()
        _cm_page_width = self.report_page_form.get_cm_page_width()

        self._pixel_columns_widths = [0 for x in range(_columns_count)]

        _fixed_columns_width = [
            num(x) if "%" not in x and num(x) != 0 else 0
            for x in self.columns_data.widths
        ]
        _procent_columns_width = [
            num(x.replace("%", "").strip()) if "%" in x else 0
            for x in self.columns_data.widths
        ]
        _float_columns_count = (
            _columns_count
            - len([x for x in _procent_columns_width if x != 0])
            - len([x for x in _fixed_columns_width if x != 0])
        )
        _procent_width = num(
            (_cm_page_width - num(sum(_fixed_columns_width))) / num(100)
        )

        for x in range(_columns_count):
            if _fixed_columns_width[x] != 0:
                self._pixel_columns_widths[x] = _fixed_columns_width[x]
            else:
                prc = _procent_columns_width[x]
                if prc == 0:
                    prc = (
                        num(100) - sum(_procent_columns_width)
                    ) / _float_columns_count
                self._pixel_columns_widths[x] = round(_procent_width * prc, 2)

        ratio = self.report_page_form.report_report_form.ratio
        self._pixel_columns_widths = [
            round(x * ratio) for x in self._pixel_columns_widths
        ]

    def clone(self):
        self.widget().add_widget_below(
            Q2ReportColumns(self.report_page_form, self.get_content()).get_widget()
        )

    def add_below(self):
        self.widget().add_widget_below(
            Q2ReportColumns(self.report_page_form, {}).get_widget()
        )

    def add_above(self):
        self.widget().add_widget_above(
            Q2ReportColumns(self.report_page_form, {}).get_widget()
        )

    def get_style(self):
        style = self.report_page_form.get_style()
        style.update(self.columns_data.get("style", {}))
        return style

    def apply_style(self):
        for row_sheet in self.get_rows_form_list():
            row_sheet.apply_style()

    def get_rows_form_list(self):
        return [x.q2_form for x in self.anchor.get_layout_widgets()[1:]]

    def get_content(self):
        rows = []
        if self.anchor is not None:
            for x in self.get_rows_form_list():
                if x.parent_rows is None:
                    rows.append(x.get_content())
        self.columns_data["rows"] = rows
        if self.columns_data.style == {}:
            del self.columns_data.style

        return self.columns_data

    def set_content(self):
        self.anchor: Q2Widget = self.w.anchor
        if self.anchor is not None:
            self.anchor.set_visible(False)
            for rowdata in self.columns_data["rows"]:
                self.anchor.add_widget_below(
                    Q2ReportRows(self, rowdata).get_widget(), -1
                )

    def after_form_show(self):
        self.columns_sheet = self.w.columns_sheet
        self.columns_sheet.set_auto_expand()
        self.columns_sheet.set_row_count(1)
        self.columns_sheet.hide_row_headers()
        self.columns_sheet.hide_column_headers()

        ReportForm.set_style_button(self, "Columns")

        self.set_content()
        self._repaint()

    def _repaint(self):
        self.columns_sheet.set_column_count(self.get_column_count())
        self.columns_sheet.set_fixed_width(
            self.report_page_form.get_pixel_page_width(), ""
        )

        self.recalc_columns_pixel_width()

        self.columns_sheet.set_cell_text(self.columns_data.widths)
        self.columns_sheet.set_column_size(
            self._pixel_columns_widths
            + [
                self.report_page_form.report_report_form.ratio * 3,
            ]
        )

        self.columns_sheet.set_cell_style_sheet(
            self.report_page_form.report_report_form.sizes_cell_style, row=0
        )
        if self.anchor is not None:
            for x in self.anchor.get_layout_widgets()[1:]:
                x.q2_form._repaint()


class Q2ReportRows(Q2Form, ReportForm):
    def __init__(self, report_columns_form: Q2ReportColumns, rows_data={}):
        super().__init__("Rows")
        self.i_am_child = True
        self.rows_sheet = None

        self.parent_rows = None

        self.children_rows = []
        self.group_mate = None
        self.table_header_rows = None
        self.table_footer_rows = None
        self.table_page_footer_rows = None

        self.spanned_cells = {}

        self.report_columns_form = report_columns_form
        self.report_report_form: Q2ReportReport = report_columns_form.report_report_form

        self.rows_data = dotdict(rows_data)

        set_dict_default(self.rows_data, "role", "free")
        set_dict_default(self.rows_data, "data_source", "")
        set_dict_default(self.rows_data, "groupby", "")
        set_dict_default(self.rows_data, "table_groups", [])
        set_dict_default(self.rows_data, "print_when", "")
        set_dict_default(self.rows_data, "print_after", "")
        set_dict_default(self.rows_data, "new_page_before", "")
        set_dict_default(self.rows_data, "new_page_after", "")

        set_dict_default(self.rows_data, "heights", ["0-0"])
        set_dict_default(self.rows_data, "style", {})
        set_dict_default(self.rows_data, "cells", {})

        self.row_actions = Q2Actions()
        self.section_action = Q2Actions()
        if 1:
            self.row_actions.add_action("Edit", self.cell_double_clicked)
            self.row_actions.add_action("-")
            self.row_actions.add_action("Height", self.edit_row_height)
            self.row_actions.add_action("-")
            self.row_actions.add_action("Add row above", self.row_add_above)
            self.row_actions.add_action("Add row below", self.row_add_below)
            self.row_actions.add_action("-")
            self.row_actions.add_action("Move row up", self.row_move_up)
            self.row_actions.add_action("Move row down", self.row_move_down)
            self.row_actions.add_action("-")
            self.row_actions.add_action("Remove row", self.row_remove)
            self.row_actions.add_action("-")
            self.row_actions.add_action("Merge selection", self.merge)
            self.row_actions.add_action("Unmerge", self.unmerge)

            self.row_actions.show_actions = 0
            self.row_actions.show_main_button = 0

            self.section_action.add_action("Edit", self.edit_data_role)
            self.section_action.add_action("Clone", self.clone)
            self.section_action.add_action("Add above", self.add_above)
            self.section_action.add_action("Add below", self.add_below)
            self.section_action.add_action("-")
            self.section_action.add_action("Move up", self.move_up)
            self.section_action.add_action("Move down", self.move_down)
            self.section_action.add_action("-")
            self.section_action.add_action("Hide/Show", self.hide_show)
            self.section_action.add_action("Remove", self.remove_me)
            self.section_action.add_action("-")
            self.section_action.add_action("Table|Add header", self.add_table_header)
            self.section_action.add_action("Table|Add footer", self.add_table_footer)
            # self.section_action.add_action("Table|Add page footer")
            self.section_action.add_action("Table|Add grouping", self.add_table_group)
            self.section_action.show_actions = 0
            self.section_action.show_main_button = 0

        self.add_control("/h")
        self.add_control(
            "style_button",
            control="sheet",
            actions=self.section_action,
            when=self.style_button_pressed,
            valid=self.style_button_pressed,
            dblclick=self.edit_data_role,
            eat_enter=1,
        )
        self.add_control(
            "rows_sheet",
            control="sheet",
            actions=self.row_actions,
            when=self.rows_sheet_focus_in,
            valid=self.rows_sheet_focus_out,
            dblclick=self.cell_double_clicked,
            eat_enter=1,
        )

    def get_rows_form_list(self):
        return self.report_columns_form.get_rows_form_list()

    def get_table_rows_index(self, rows: ReportForm, crows):
        cur = crows.index(self)
        if rows.rows_data.role == "free":
            von = bis = crows.index(rows)
        else:
            master_rows = rows.parent_rows
            if master_rows is None:
                master_rows = rows
            bis = crows.index(master_rows)
            von = bis
            for x in master_rows.children_rows + [master_rows]:
                von = min(von, crows.index(x))
                bis = max(bis, crows.index(x))
        return (von, cur, bis)

    def swap_groups(self, von, cur, bis, swap, crows):
        for master in range(von, bis + 1):
            if crows[master].rows_data.role == "table":
                mcur = master - cur + master
                mswap = master - swap + master
                break
        ReportForm.move_down(crows[min(cur, swap)])
        ReportForm.move_down(crows[min(mcur, mswap)])

    def move_down(self):
        crows = self.get_rows_form_list()
        # try to swap group rows
        von, cur, bis = self.get_table_rows_index(self, crows)
        if self.rows_data.role.startswith("group_"):
            if len(self.parent_rows.rows_data.table_groups) > 1:
                if crows[cur + 1].rows_data.role.startswith("group"):
                    self.swap_groups(von, cur, bis, cur + 1, crows)
                    return

        if bis == len(crows) - 1:
            return
        von2, cur2, bis2 = self.get_table_rows_index(crows[bis + 1], crows)

        for x in range(bis, von - 1, -1):
            for y in range(bis2 - von2 + 1):
                ReportForm.move_down(crows[x])

    def move_up(self):
        crows = self.get_rows_form_list()
        # try to swap group rows
        von, cur, bis = self.get_table_rows_index(self, crows)
        if self.rows_data.role.startswith("group_"):
            if len(self.parent_rows.rows_data.table_groups) > 1:
                if crows[cur - 1].rows_data.role.startswith("group"):
                    self.swap_groups(von, cur, bis, cur - 1, crows)
                    return

        von, cur, bis = self.get_table_rows_index(self, crows)
        if von == 0:
            return
        von2, cur2, bis2 = self.get_table_rows_index(crows[von - 1], crows)

        for x in range(von, bis + 1):
            for y in range(bis2 - von2 + 1):
                ReportForm.move_up(crows[x])

    def column_remove(self, current_column):
        self.rows_sheet.remove_column(current_column)
        tmp = {}
        for cell_key in list(self.rows_data.cells.keys()):
            key = [int_(y) for y in cell_key.split(",")]
            if key[1] == current_column:
                del self.rows_data.cells[cell_key]
            elif key[1] > current_column:
                tmp[f"{key[0]},{key[1]-1}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
            elif key[1] <= current_column:
                if self.rows_data.cells[cell_key].get("colspan", 0) > 1:
                    tmp[cell_key] = self.rows_data.cells[cell_key]
                    tmp[cell_key]["colspan"] = tmp[cell_key]["colspan"] - 1

        self.rows_data.cells.update(tmp)

    def column_move(self, current_column):
        tmp = {}
        for cell_key in list(self.rows_data.cells.keys()):
            key = [int_(y) for y in cell_key.split(",")]
            if key[1] not in [current_column, current_column + 1]:
                continue
            if key[1] == current_column:
                tmp[f"{key[0]},{key[1]+1}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
            elif key[1] == current_column + 1:
                tmp[f"{key[0]},{key[1]-1}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
        self.rows_data.cells.update(tmp)

        self.rows_sheet.move_column(current_column)
        self._repaint()

    def column_insert(self, current_column):
        self.rows_sheet.insert_column(current_column)
        tmp = {}
        for cell_key in list(self.rows_data.cells.keys()):
            key = [int_(y) for y in cell_key.split(",")]
            if key[1] >= current_column:
                tmp[f"{key[0]},{key[1]+1}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
            elif key[1] <= current_column:
                if (
                    key[1] + self.rows_data.cells[cell_key].get("colspan", 0)
                    > current_column
                ):
                    tmp[cell_key] = self.rows_data.cells[cell_key]
                    tmp[cell_key]["colspan"] = tmp[cell_key]["colspan"] + 1

        self.rows_data.cells.update(tmp)
        self._repaint()

    def row_remove(self):
        selected_rows = self.get_selected_rows()
        selected_rows.reverse()
        for current_row in selected_rows:
            current_row = self.rows_sheet.current_row()
            self.rows_data.heights.pop(current_row)
            self.rows_sheet.remove_row(current_row)
            tmp = {}
            for cell_key in list(self.rows_data.cells.keys()):
                key = [int_(y) for y in cell_key.split(",")]
                if key[0] == current_row:
                    del self.rows_data.cells[cell_key]
                elif key[0] > current_row:
                    tmp[f"{key[0]-1},{key[1]}"] = self.rows_data.cells[cell_key]
                    del self.rows_data.cells[cell_key]
                elif key[0] <= current_row:
                    if self.rows_data.cells[cell_key].get("rowspan", 0) > 1:
                        tmp[cell_key] = self.rows_data.cells[cell_key]
                        tmp[cell_key]["rowspan"] = tmp[cell_key]["rowspan"] - 1
            self.rows_data.cells.update(tmp)
        self._repaint()

    def get_selected_rows(self):
        return list(set([x[0] for x in self.rows_sheet.get_selection()]))

    def is_row_span_intersection(self, current_row):
        return False

    def row_move(self, current_row):
        if current_row >= self.get_row_count() - 1 or current_row < 0:
            return

        if self.is_row_span_intersection(current_row):
            return

        tmph = self.rows_data.heights[current_row]
        self.rows_data.heights[current_row] = self.rows_data.heights[current_row + 1]
        self.rows_data.heights[current_row + 1] = tmph

        tmp = {}
        for cell_key in list(self.rows_data.cells.keys()):
            key = [int_(y) for y in cell_key.split(",")]
            if key[0] not in [current_row, current_row + 1]:
                continue
            if key[0] == current_row:
                tmp[f"{key[0]+1},{key[1]}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
            elif key[0] == current_row + 1:
                tmp[f"{key[0]-1},{key[1]}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
        self.rows_data.cells.update(tmp)

        self.rows_sheet.move_row(current_row)
        self._repaint()

    def row_move_up(self):
        self.row_move(self.rows_sheet.current_row() - 1)

    def row_move_down(self):
        self.row_move(self.rows_sheet.current_row())

    def row_add(self, current_row=None):
        self.rows_sheet.insert_row(current_row)
        self.rows_data.heights.insert(current_row, "0-0")
        tmp = {}
        for cell_key in list(self.rows_data.cells.keys()):
            key = [int_(y) for y in cell_key.split(",")]
            if key[0] >= current_row:
                tmp[f"{key[0]+1},{key[1]}"] = self.rows_data.cells[cell_key]
                del self.rows_data.cells[cell_key]
            elif key[0] <= current_row:
                if (
                    key[0] + self.rows_data.cells[cell_key].get("rowspan", 1)
                    > current_row
                ):
                    tmp[cell_key] = self.rows_data.cells[cell_key]
                    tmp[cell_key]["rowspan"] = tmp[cell_key]["rowspan"] + 1
        self.rows_data.cells.update(tmp)
        self._repaint()

    def row_add_above(self):
        self.row_add(self.rows_sheet.current_row())

    def row_add_below(self):
        self.row_add(self.rows_sheet.current_row() + 1)

    def cell_double_clicked(self):
        current_column = self.rows_sheet.current_column()
        # elif current_column > self.report_columns_form.get_column_count():
        if self.focus_widget() == self.w.style_button:
            self.edit_data_role()
        elif current_column == self.report_columns_form.get_column_count():
            self.edit_row_height()
        else:
            self.edit_cell_content()

    def edit_cell_content(self):
        form = Q2Form(_("Enter row height"))
        form.add_control("/h")
        form.add_control("content", control="code", data=self.rows_sheet.get_text())
        form.ok_button = 1
        form.cancel_button = 1

        def after_form_show():
            form.w._ok_button.set_focus()

        form.after_form_show = after_form_show
        form.run()
        if form.ok_pressed:
            key = f"{self.rows_sheet.current_row()},{self.rows_sheet.current_column()}"
            if key not in self.rows_data.cells:
                self.rows_data.cells[key] = {}
            self.rows_data.cells[key]["data"] = form.s.content
            self.rows_sheet.set_text(form.s.content)
            self._repaint()

    def edit_row_height(self):
        height = self.rows_sheet.get_cell_text(
            row=self.rows_sheet.current_row(),
            column=self.report_columns_form.get_column_count(),
        ).split("-")

        form = Q2Form(_("Enter row height"))
        form.do_not_save_geometry = 1
        form.add_control(
            "h0",
            _("Column height min"),
            control="line",
            datatype="dec",
            datalen=5,
            datadec=2,
            data=height[0],
        )
        form.add_control(
            "h1",
            _("Column height max"),
            control="line",
            datatype="dec",
            datalen=5,
            datadec=2,
            data=height[1],
        )
        form.add_control("/")
        form.add_control("/h", "-")
        form.add_control("/s")

        def set_defaulf():
            form.s.h0 = "0"
            form.s.h1 = "0"

        form.add_control("", _("Set default"), control="button", valid=set_defaulf)
        form.add_control("/s")
        form.ok_button = 1
        form.cancel_button = 1
        form.run()
        if form.ok_pressed:
            h0 = 0 if num(form.s.h0) == 0 else num(form.s.h0)
            h1 = 0 if num(form.s.h1) == 0 else num(form.s.h1)
            self.rows_data.heights[self.rows_sheet.current_row()] = f"{h0}-{h1}"
            self._repaint()

    def edit_data_role(self):
        form = Q2Form(_("Rows data role"))
        form.do_not_save_geometry = 1
        form.ok_button = 1
        form.cancel_button = 1

        roles_list = "free;table;tree;header;footer"

        def role_valid():
            form.w.data_source.set_disabled(form.s.role != "table")
            if form.w.group:
                form.w.group.set_disabled(form.s.role != "table")

        if self.rows_data.role in roles_list.split(";"):
            # role is selectable - if not group rows
            form.add_control(
                "role",
                _("Role"),
                control="combo",
                datatype="char",
                data=self.rows_data.role,
                pic=roles_list,
                datalen=50,
                valid=role_valid,
            )
            form.add_control(
                "data_source",
                _("Datasource"),
                data=self.rows_data.data_source,
                disabled=self.rows_data.role != "table",
                datalen=100,
            )

        if self.rows_data.role in ["group_header", "group_footer"]:  # group
            form.add_control(
                "groupby",
                _("Grouping"),
                datalen=50,
                data=self.rows_data.groupby,
                disabled=0,
            )

        form.add_control("print_when", _("Print when"), data=self.rows_data.print_when)
        form.add_control(
            "print_after", _("After print"), data=self.rows_data.print_after
        )
        form.add_control("/")
        form.add_control("/h")
        form.add_control(
            "new_page_before",
            _("New page before"),
            control="check",
            data=self.rows_data.new_page_before,
        )
        form.add_control(
            "new_page_after",
            _("New page after"),
            control="check",
            data=self.rows_data.new_page_after,
        )
        form.add_control("/")

        form.run()
        if form.ok_pressed:
            # proceed = False23
            last_role = self.rows_data.role
            if self.rows_data.role == "table" and form.s.role != "table":
                proceed = q2AskYN(_("It will remove all siblings! Proceed?")) == 2
                proceed = True
                if proceed:
                    form.s.data_source = ""
                    for x in self.children_rows:
                        x.widget().remove()

            if last_role in roles_list.split(";"):  # skip table children
                self.rows_data.role = form.s.role
                self.rows_data.data_source = form.s.data_source

            if self.group_mate:
                self.rows_data.groupby = form.s.groupby
                self.group_mate.rows_data.groupby = form.s.groupby
                self.group_mate.set_rows_role_text()

            self.rows_data.print_when = form.s.print_when
            self.rows_data.print_after = form.s.print_after
            self.rows_data.new_page_before = form.s.new_page_before
            self.rows_data.new_page_after = form.s.new_page_after

            if last_role != "table" and form.s.role == "table":  # is is table now
                self.add_table_header()
                self.add_table_footer()

            self.set_rows_role_text()

    def style_button_pressed(self):
        self.w.style_button.action_set_visible("Table", self.rows_data.role == "table")
        self.report_report_form.focus_changed(self.w.style_button)
        self.report_report_form.update_style_bar(self.get_style(), self.rows_data.style)

    def merge(self):
        sel = self.rows_sheet.get_selection()
        row = min(sel)[0]
        column = min(sel)[1]
        cell_key = f"{row},{column}"
        rowspan = max(sel)[0] - row + 1
        colspan = max(sel)[1] - column + 1

        self.rows_data.cells[cell_key]["rowspan"] = rowspan
        self.rows_data.cells[cell_key]["colspan"] = colspan
        self.apply_style()
        self.rows_sheet.set_current_cell(row, column)

    def unmerge(self):
        row = self.rows_sheet.current_row()
        column = self.rows_sheet.current_column()
        cell_key = f"{row},{column}"

        row_span = self.rows_data.cells[cell_key]["rowspan"]
        col_span = self.rows_data.cells[cell_key]["colspan"]
        for r in range(row, row + row_span):  # set data into unspanned cells
            for c in range(column, column + col_span):
                if r != row or c != column:
                    cell_data = self.rows_data.cells.get(f"{r},{c}", {})
                    self.rows_sheet.set_cell_text(cell_data.get("data", ""), r, c)

        self.rows_sheet.clear_spans()
        del self.rows_data.cells[cell_key]["rowspan"]
        del self.rows_data.cells[cell_key]["colspan"]
        self.rows_sheet.set_current_cell(row, column)
        self.rows_sheet_focus_in()
        self.apply_style()

    def can_i_merge(self):
        selection = self.rows_sheet.get_selection()
        if len(selection) == 1:
            return False
        #  megre merged cells
        # _selection = []
        # for x in selection:
        #     if x not in self.spanned_cells:
        #         continue
        #     for _row in range(x[0], self.spanned_cells[x][0] + 1):
        #         for _col in range(x[1], self.spanned_cells[x][1] + 1):
        #             if _row == x[0] and _col == x[1]:
        #                 continue
        #             _selection.append((_row, _col))
        # selection.extend(_selection)

        rows = set([x[0] for x in selection])
        cols = set([x[1] for x in selection])

        if len(selection) != len(rows) * len(cols):
            return False
        elif len(rows) == 0 or len(rows) != max(rows) - min(rows) + 1:
            return False
        elif max(cols) == self.report_columns_form.get_column_count():
            return False
        elif len(cols) == 0 or len(cols) != max(cols) - min(cols) + 1:
            return False
        return True

    def can_i_unmerge(self):
        selection = self.rows_sheet.get_selection()
        if len(selection) != 1:
            return False

        row = self.rows_sheet.current_row()
        column = self.rows_sheet.current_column()
        return (row, column) in self.spanned_cells

    def rows_sheet_focus_in(self):
        self.rows_sheet.action_set_visible("Unmerge", self.can_i_unmerge())
        self.rows_sheet.action_set_visible("Merge selection", self.can_i_merge())
        self.rows_sheet.action_set_visible("Move row up", len(self.spanned_cells) == 0)
        self.rows_sheet.action_set_visible(
            "Move row down", len(self.spanned_cells) == 0
        )

        all_style = self.get_style()

        row = self.rows_sheet.current_row()
        column = self.rows_sheet.current_column()
        cell_key = f"{row},{column}"
        if cell_key not in self.rows_data.cells:
            self.rows_data.cells[cell_key] = {}
        set_dict_default(self.rows_data.cells[cell_key], "data", "")
        set_dict_default(self.rows_data.cells[cell_key], "style", {})

        all_style.update(self.rows_data.cells[cell_key]["style"])

        self.report_report_form.focus_changed(self.rows_sheet)
        self.report_report_form.update_style_bar(
            all_style, self.rows_data.cells[cell_key]["style"]
        )

    def rows_sheet_focus_out(self):
        pass

    def clone(self):
        crows = self.get_rows_form_list()
        von, cur, bis = self.get_table_rows_index(self, crows)
        clone = Q2ReportRows(self.report_columns_form, self.get_content())
        if bis != von:  # part of table rows
            if clone.rows_data.role != "table":
                clone.rows_data.role = "free"
            crows[bis].widget().add_widget_below(clone.get_widget())
        else:
            self.widget().add_widget_below(clone.get_widget())

    def add_below(self):
        crows = self.get_rows_form_list()
        von, cur, bis = self.get_table_rows_index(self, crows)

        self.widget().add_widget_below(
            Q2ReportRows(self.report_columns_form, {}).get_widget(), bis - cur
        )

    def add_above(self):
        crows = self.get_rows_form_list()
        von, cur, bis = self.get_table_rows_index(self, crows)
        cur = crows.index(self)

        self.widget().add_widget_above(
            Q2ReportRows(self.report_columns_form, {}).get_widget(), cur - von
        )

    def hide_show(self):
        if self.rows_sheet is None:
            return
        # take care about children
        for x in self.children_rows:
            x.widget().set_visible(not self.rows_sheet.is_visible())
        self.rows_sheet.set_visible(not self.rows_sheet.is_visible())
        # adjust style_sheet
        need_height = self.w.style_button.get_cell_widget(0, 0).get_default_height()
        if not self.rows_sheet.is_visible():
            self.w.style_button.set_row_size(need_height, 0)
        else:
            need_height = max(self.rows_sheet.height(), need_height)
            self.w.style_button.set_row_size(need_height, 0)

    def get_row_count(self):
        return len(self.rows_data.heights)

    def get_content(self):
        if self.rows_data.style == {}:
            del self.rows_data.style
        cell2del = []
        for x in self.rows_data.cells:
            if self.rows_data.cells[x].get("style") == {}:
                del self.rows_data.cells[x]["style"]
            if self.rows_data.cells[x].get("data") == "":
                del self.rows_data.cells[x]["data"]
            if self.rows_data.cells[x] == {}:
                cell2del.append(x)

        for x in cell2del:
            del self.rows_data.cells[x]

        if self.table_header_rows:
            self.rows_data["table_header"] = self.table_header_rows.get_content()

        if self.table_footer_rows:
            self.rows_data["table_footer"] = self.table_footer_rows.get_content()

        group_data = []
        group_rows = []
        if self.rows_data.role == "table":
            for x in self.get_rows_form_list():
                if x.rows_data.role.startswith("group_"):
                    group_rows.append(x)
        for x in range(int(len(group_rows) / 2)):
            group_data.append(
                {
                    "group_header": group_rows[x].get_content(),
                    "group_footer": group_rows[-(x + 1)].get_content(),
                }
            )
        self.rows_data["table_groups"] = group_data

        return self.rows_data

    def get_style(self):
        style = self.report_columns_form.get_style()
        style.update(self.rows_data.get("style", {}))
        return style

    def set_content(self):
        for row in range(self.get_row_count()):
            for column in range(self.report_columns_form.get_column_count()):
                cell_data = self.rows_data.cells.get(f"{row},{column}", {})
                self.rows_sheet.set_cell_text(cell_data.get("data", ""), row, column)

        self.apply_style()

        if self.rows_data.role == "table":
            for group in self.rows_data.get("table_groups"):
                self.add_table_group(group)
            if self.rows_data.get("table_header"):
                self.add_table_header(self.rows_data.get("table_header"))
            if self.rows_data.get("table_footer"):
                self.add_table_footer(self.rows_data.get("table_footer"))

    def apply_style(self):
        self.rows_sheet.sheet_styles = self.get_style()
        self.rows_sheet.cell_styles = {}
        self.rows_sheet.clear_spans()
        self.spanned_cells = {}
        for row in range(self.get_row_count()):
            for column in range(self.report_columns_form.get_column_count()):
                cell_data = self.rows_data.cells.get(f"{row},{column}", {})

                self.rows_sheet.cell_styles[f"{row},{column}"] = cell_data.get(
                    "style", {}
                )
                rowspan = cell_data.get("rowspan", 1)
                colspan = cell_data.get("colspan", 1)
                if rowspan > 1 or colspan > 1:
                    self.spanned_cells[(row, column)] = (rowspan, colspan)
                    self.rows_sheet.set_span(row, column, rowspan, colspan)
                self.rows_sheet.set_cell_style_sheet(None, row, column)

    def add_table_header(self, header_data={}):
        if self.rows_data.role != "table":
            return
        if self.table_header_rows:
            return
        if not isinstance(header_data, dict):
            header_data = {}
        header_data["role"] = "table_header"
        table_header_rows = Q2ReportRows(self.report_columns_form, header_data)
        table_header_rows.parent_rows = self
        self.children_rows.append(table_header_rows)
        self.table_header_rows = table_header_rows
        self.rows_data["table_header"] = header_data
        self.widget().add_widget_above(
            table_header_rows.get_widget(), len(self.rows_data["table_groups"])
        )

    def add_table_footer(self, footer_data={}):
        if self.rows_data.role != "table":
            return
        if self.table_footer_rows:
            return
        if not isinstance(footer_data, dict):
            footer_data = {}
        footer_data["role"] = "table_footer"
        table_footer_rows = Q2ReportRows(self.report_columns_form, footer_data)
        table_footer_rows.parent_rows = self
        self.children_rows.append(table_footer_rows)
        self.table_footer_rows = table_footer_rows
        self.rows_data["table_footer"] = footer_data
        self.widget().add_widget_below(
            table_footer_rows.get_widget(), len(self.rows_data["table_groups"])
        )

    def add_table_group(self, group_data=None):
        if not isinstance(group_data, dict):
            group_data = dotdict()
            self.rows_data["table_groups"].insert(0, group_data)

        # set_dict_default(group_data, "group_header", {"cells": {"0,0": {"data": ""}}})
        # set_dict_default(group_data, "group_footer", {"cells": {"0,0": {"data": ""}}})
        set_dict_default(group_data, "group_header", {"cells": {}})
        set_dict_default(group_data, "group_footer", {"cells": {}})

        group_data["group_header"]["role"] = "group_header"
        group_data["group_footer"]["role"] = "group_footer"

        group_header = Q2ReportRows(
            self.report_columns_form, group_data["group_header"]
        )
        group_footer = Q2ReportRows(
            self.report_columns_form, group_data["group_footer"]
        )

        group_header.group_mate = group_footer
        group_footer.group_mate = group_header

        if self.rows_data.role == "table":
            master_rows = self
        else:
            master_rows = self.parent_rows

        master_rows.widget().add_widget_above(group_header.get_widget())
        master_rows.widget().add_widget_below(group_footer.get_widget())

        group_header.parent_rows = self
        self.children_rows.append(group_header)
        group_footer.parent_rows = self
        self.children_rows.append(group_footer)

    def after_form_show(self):
        self.rows_sheet = self.w.rows_sheet
        if self.rows_sheet is None:
            return
        self.rows_sheet.set_auto_expand()
        self.rows_sheet.hide_row_headers()
        self.rows_sheet.hide_column_headers()
        self.rows_sheet.add_style_sheet("border-style:solid; border-radius:0")

        ReportForm.set_style_button(self)

        self._repaint()
        self.set_content()

    def remove_me(self):
        crows = self.get_rows_form_list()
        von, cur, bis = self.get_table_rows_index(self, crows)
        if bis - von + 1 == len(crows) and self.parent_rows is None:
            return

        if q2AskYN(_("Remove rows?")) != 2:
            return

        if self.rows_data.role.startswith("group_"):
            for master in range(von, bis + 1):
                if crows[master].rows_data.role == "table":
                    mcur = master - cur + master
                    break
            self.parent_rows.rows_data.table_groups.pop(abs(cur - master) - 1)
            for x in [cur, mcur]:
                crows[x].widget().remove()
                pos = self.parent_rows.children_rows.index(crows[x])
                self.parent_rows.children_rows.pop(pos)
        else:
            self.widget().remove()

        if self.rows_data.role in ["table_header"]:
            self.parent_rows.table_header_rows = None
            del self.parent_rows.rows_data["table_header"]
            pos = self.parent_rows.children_rows.index(self)
            self.parent_rows.children_rows.pop(pos)

        elif self.rows_data.role in ["table_footer"]:
            self.parent_rows.table_footer_rows = None
            del self.parent_rows.rows_data["table_footer"]
            pos = self.parent_rows.children_rows.index(self)
            self.parent_rows.children_rows.pop(pos)
        elif self.rows_data.role in ["table"]:
            for x in self.children_rows:
                x.widget().remove()

    def set_rows_role_text(self):
        role_text = f"""<b>{self.rows_data.role}</b>"""

        if self.rows_data.role == "table":
            role_text += f"<br>{self.rows_data.data_source}"

        if self.rows_data.role.startswith("group"):
            role_text += f"<br><i>{self.rows_data.groupby}</i>"

        self.set_style_button_text(role_text)
        need_height = self.w.style_button.get_cell_widget(0, 0).get_default_height()

        if self.w.style_button.get_row_size(0) < need_height:
            self.w.style_button.set_row_size(need_height, 0)

    def _repaint(self):
        if self.rows_sheet is None:
            return

        ratio = self.report_columns_form.report_page_form.report_report_form.ratio
        self.apply_style()
        self.rows_sheet.set_row_count(self.get_row_count())
        self.rows_sheet.set_column_count(
            self.report_columns_form.get_column_count() + 1
        )

        self.rows_sheet.set_fixed_width(
            self.report_columns_form.report_page_form.get_pixel_page_width(), ""
        )
        for i, x in enumerate(self.rows_data.heights):
            h = max([num(h) for h in x.split("-")] + [0.7])
            self.rows_sheet.set_row_size(h * ratio, i)

        self.rows_sheet.set_column_size(
            self.report_columns_form._pixel_columns_widths + [ratio]
        )

        self.rows_sheet.set_cell_style_sheet(
            self.report_columns_form.report_page_form.report_report_form.sizes_cell_style,
            column=self.report_columns_form.get_column_count(),
        )

        self.rows_sheet.set_cell_text(
            self.rows_data.heights, column=self.report_columns_form.get_column_count()
        )

        self.w.style_button.set_row_size(self.rows_sheet.height())

        self.set_rows_role_text()
