if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()


from q2db.cursor import Q2Cursor
from q2gui.q2model import Q2CursorModel, Q2Model
from q2gui.q2app import Q2Actions
from q2rad.q2raddb import q2cursor
from q2gui.q2utils import set_dict_default
import json
import gettext
import re
from q2rad import Q2Form

_ = gettext.gettext
re_find_param = re.compile(r":\b\w+\b")


class Q2Queries(Q2Form):
    def __init__(self):
        super().__init__("Queries")
        self.no_view_action = True

    def on_init(self):
        self.create_form()

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="queries")
        model = Q2CursorModel(cursor)
        model.set_order("name").refresh()
        self.set_model(model)
        self.add_action("/crud")
        self.add_action("JSON", self.edit_json)

    def create_form(self):
        self.query_editor_form = Q2QueryEdit()

        self.add_control("name", _("Name"), datatype="char", datalen=100, pk="*")
        self.add_control("/")
        self.add_control(
            "query_edit", "", widget=self.query_editor_form, nogrid=1, migrate=0
        )

        self.add_control(
            "content",
            "",
            datatype="bigtext",
            control="codejson",
            nogrid=1,
            noform=1,
            # readonly=1,
        )
        self.add_control("comment", _("Comment"), datatype="text", noform=1)

    def after_form_show(self):
        if self.crud_mode == "NEW":
            self.query_editor_form.set_content("{}")
        else:
            self.query_editor_form.set_content(self.r.content)
        self.query_editor_form.query_list.set_grid_index(0)
        self.query_editor_form.query_list.w.form__grid.set_focus()

    def before_crud_save(self):
        self.s.content = self.query_editor_form.get_content()

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


class Q2QueryEdit(Q2Form):
    def __init__(self):
        super().__init__("Query Edit")
        self.no_view_action = True
        self.lock_code_widget = False

    def on_init(self):
        self.query_list = Q2QueryList(self)
        self.param_list = Q2ParamList()
        self.actions = Q2Actions()
        self.actions.add_action("Run F4", self.query_list.sql_runner, hotkey="F4")

        self.actions.show_main_button = 0
        self.actions.show_actions = 0
        self.add_control("/hs", tag="qeh")
        self.add_control("hot_key_action", actions=self.actions, control="toolbar")
        if self.add_control("/vs", tag="qev"):
            self.add_control("ql", "", widget=self.query_list, nogrid=1, migrate=0)
            self.add_control(
                "run_query_button",
                "Run (F4)",
                valid=self.query_list.sql_runner,
                control="button",
            )
            self.add_control("pl", "", widget=self.param_list, nogrid=1, migrate=0)
            self.add_control("/")
        self.add_control("code", control="codesql", nogrid=1, valid=self.sql_changed)

    def set_content(self, content):
        if isinstance(content, str):
            content_json = json.loads(content)
        else:
            content_json = content
        self.query_list.set_content(
            content_json.get(
                "queries", {"new_query":"select * from "}
            )
        )
        self.param_list.set_content(content_json.get("params", []))
        self.param_list.put_params(self.get_all_sql())

    def get_content(self, str_mode=True):
        queries = self.query_list.get_content()
        params = self.param_list.get_content()

        content = {"queries": queries, "params": params}
        if str_mode:
            return json.dumps(content, indent=2)
        else:
            return content

    def after_form_show(self):
        self.w.run_query_button.fix_default_height()
        self.w.hot_key_action.set_visible(0)
        self.query_list.grid_index_changed()

    def sql_changed(self):
        if self.lock_code_widget is True:
            return
        self.query_list.sql_to_model(self.s.code)
        self.param_list.put_params(self.get_all_sql())

    def get_all_sql(self):
        return " ".join([x.get("sql", "") for x in self.query_list.model.records])


class Q2QueryList(Q2Form):
    def __init__(self, query_editor_form):
        super().__init__("QueryList")
        self.i_am_child = True
        self.query_editor_form = query_editor_form
        self.no_view_action = True
        self.add_control("name", "Name", datatype="char", datalen="50")
        self.add_control("sql", "Sql", datatype="bigtext", nogrid=1, noform=1)
        self.set_model(Q2Model())
        self.add_action("/crud")
        self.model.readonly = False
        self.last_current_row = -1

    def set_content(self, content):
        self.model.reset()
        for x in content:
            self.model.insert({"name": x, "sql": content[x]})
        self.refresh()

    def sql_runner(self):
        sql = self.r.sql
        params = re_find_param.findall(sql)
        for x in params:
            value = self.query_editor_form.param_list.get_param(x)
            sql = sql.replace(x, f"'{value}'")
        q2cursor(sql).browse()

    def sql_to_model(self, sql):
        self.model.update({"sql": sql}, self.current_row, refresh=False)

    def grid_index_changed(self):
        if self.current_row < 0:
            return
        sql = self.model.get_record(self.current_row).get("sql", "")
        self.query_editor_form.lock_code_widget = True
        self.query_editor_form.s.code = sql
        self.query_editor_form.lock_code_widget = False

    def before_crud_save(self):
        if self.crud_mode == "NEW":
            self.s.sql = "select *\nfrom "

    def get_content(self):
        content = {x["name"]: x["sql"] for x in self.model.records}
        return content


class Q2ParamList(Q2Form):
    def __init__(self):
        super().__init__("ParamList")
        self.i_am_child = True
        self.no_view_action = True
        self.add_control("name", "Name", datatype="char", datalen="50", disabled="*")
        self.add_control("value", "Value", datatype="text", control="codesql")
        self.add_control(
            "hidden", "Hidden", datatype="char", datalen=1, nogrid=1, noform=1
        )
        self.set_model(Q2Model())
        self.add_action_edit()
        self.model.readonly = False

    def set_content(self, content):
        content = [{"name": x, "value": content[x]} for x in content]
        self.model.reset()
        names = []
        for x in content:
            set_dict_default(x, "name", "name")
            if x["name"] in names:
                continue
            else:
                names.append(x["name"])
            set_dict_default(x, "value", "")
            set_dict_default(x, "hidden", "")
            self.model.insert(x)

    def get_content(self):
        params = {}
        for param in self.model.records:
            param = dict(param)
            if param["hidden"] != "":
                continue
            del param["hidden"]
            params[param["name"]] = param["value"]
        return params

    def get_param(self, param):
        for x in self.model.records:
            if x["name"] == param[1:]:
                return x["value"]
        return ""

    def put_params(self, sql):
        params = set(re_find_param.findall(sql))
        params = {x[1:] for x in params}
        names = {}
        for x in range(len(self.model.records)):
            names[self.model.records[x]["name"]] = x
        for x in params:
            if x in names:
                self.model.records[names[x]]["hidden"] = ""
            else:
                self.model.insert({"name": x, "value": "", "hidden": ""})
        for x in names:
            if x not in params:
                self.model.records[names[x]]["hidden"] = "*"

        self.model.set_order("name")
        self.model.set_where("hidden==''")
