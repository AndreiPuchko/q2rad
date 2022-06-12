if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")


from q2rad import Q2App, Q2Form

from q2gui.q2dialogs import q2Mess
from q2gui.q2model import Q2CursorModel
from q2db.schema import Q2DbSchema
from q2db.db import Q2Db
from q2rad.q2actions import Q2Actions
from q2db.cursor import Q2Cursor

from q2rad.q2raddb import q2cursor

# from random import randint

from q2rad.q2appselector import Q2AppSelect
from q2rad.q2modules import Q2Modules
from q2rad.q2forms import Q2Forms
from q2rad.q2lines import Q2Lines
from q2rad.q2queries import Q2Queries
from q2rad.q2reports import Q2Reports

import traceback
import gettext


_ = gettext.gettext


class Q2RadApp(Q2App):
    def __init__(self, title=""):
        super().__init__(title)
        self.db = None
        self.db_data = None
        self.db_logic = None
        self.dev_mode = False

    def on_start(self):
        self.open_application(autoload_enabled=True)

    def open_application(self, autoload_enabled=False):
        app_selector = Q2AppSelect().run(autoload_enabled)
        self.selected_application = app_selector.selected_application
        if self.selected_application != {}:
            self.open_selected_app()
        else:
            self.close()

    def open_selected_app(self):
        self.open_databases()
        self.migrate_db_logic()
        self.migrate_db_data()
        self.create_menu()
        # DEBUG
        # self.run_forms()
        # self.run_queries()
        # self.run_modules()
        self.run_reports()
        pass

    def migrate_db_data(self):
        data_schema = Q2DbSchema()
        cu = q2cursor(
            """
                select
                    forms.form_table as `table`
                    , lines.name as column
                    , lines.datatype
                    , lines.datalen
                    , lines.datadec
                    , lines.to_table
                    , lines.to_column
                    , lines.related
                    , lines.ai
                    , lines.pk
                from lines, forms
                where forms.form_name = lines.form_name
                    and form_table <>'' and migrate <>''
                """,
            self.db_logic,
        )
        for column in cu.records():
            data_schema.add(**column)
        self.db_data.set_schema(data_schema)
        self.create_menu()

    def migrate_db_logic(self):
        data_schema = Q2DbSchema()
        for form in (
            Q2Modules(),
            Q2Forms(),
            Q2Lines(),
            Q2Queries(),
            Q2Actions(),
            Q2Reports(),
        ):
            for x in form.get_table_schema():
                data_schema.add(**x)
        self.db_logic.set_schema(data_schema)

    def open_databases(self):
        self.db_data = Q2Db(database_name=self.selected_application["database_data"])
        # self.db_logic.cursor("drop table lines")
        self.db_logic = Q2Db(database_name=self.selected_application["database_logic"])

    def create_menu(self):
        self.clear_menu()
        self.add_menu("File|About", lambda: q2Mess("q2RAD"))
        self.add_menu("File|-")
        self.add_menu("File|Open", self.open_application)
        self.add_menu("File|-")
        self.add_menu("File|Close", self.close, toolbar=1)

        self.create_form_menu()

        self.add_menu("Dev|Forms", self.run_forms, toolbar=self.dev_mode)
        self.add_menu("Dev|Modules", self.run_modules, toolbar=self.dev_mode)
        self.add_menu("Dev|Querys", self.run_queries, toolbar=self.dev_mode)
        self.add_menu("Dev|Reports", self.run_reports, toolbar=self.dev_mode)
        self.build_menu()

    def create_form_menu(self):
        cu = q2cursor(
            """select
                menu_path
                , title
                , toolbar
                , menu_text
                , menu_before
                , menu_tiptext
                , menu_separator
                , form_name
            from forms
            where menu_path <> ''
            order by seq
            """,
            self.db_logic,
        )
        for x in cu.records():
            menu_path = (
                x["menu_path"]
                + "|"
                + (x["menu_text"] if x["menu_text"] else x["title"])
            )

            def menu_worker(form_name):
                def real_worker():
                    self.run_form(form_name)

                return real_worker

            self.add_menu(
                menu_path,
                worker=menu_worker(x["form_name"]),
                toolbar=x["toolbar"],
                before=x["menu_before"],
            )

    def run_forms(self):
        Q2Forms().run()

    def run_modules(self):
        Q2Modules().run()

    def run_queries(self):
        Q2Queries().run()

    def run_reports(self):
        Q2Reports().run()

    def run_form(self, form_name):
        self.get_form(form_name).run()

    def get_form(self, form_name):
        form_dic = self.db_logic.get("forms", f"form_name ='{form_name}'")

        sql = f"""
            select
                name
                ,label
                ,gridlabel
                ,nogrid
                ,noform
                ,`check`
                ,control
                ,pic
                ,datatype
                ,datalen
                ,datadec
                ,migrate
                ,pk
                ,ai
                ,to_table
                ,to_column
                ,related
                ,to_form
            from lines
            where form_name = '{form_name}'
            order by seq
            """
        cu = q2cursor(sql, self.db_logic)

        form = Q2Form(form_dic["title"])
        form.no_view_action = 1
        form.ok_button = form_dic["ok_button"]
        form.cancel_button = form_dic["cancel_button"]

        form.valid = self.code_runner(form_dic["form_valid"], form)

        form.before_form_build = self.code_runner(form_dic["before_form_build"], form)
        form.before_grid_build = self.code_runner(form_dic["before_grid_build"], form)

        form.before_form_show = self.code_runner(form_dic["before_form_show"], form)
        form.after_form_show = self.code_runner(form_dic["after_form_show"], form)

        form.before_grid_show = self.code_runner(form_dic["before_grid_show"], form)
        form.after_grid_show = self.code_runner(form_dic["after_grid_show"], form)

        form.before_crud_save = self.code_runner(form_dic["before_crud_save"], form)
        form.after_crud_save = self.code_runner(form_dic["after_crud_save"], form)

        form.before_delete = self.code_runner(form_dic["before_delete"], form)
        form.after_delete = self.code_runner(form_dic["after_delete"], form)

        # add controls
        for x in cu.records():
            if x.get("to_form"):
                x["to_form"] = self.get_form(x["to_form"])
            form.add_control(**x)

        # add actions
        if form_dic["form_table"]:
            form_cursor: Q2Cursor = self.db_data.table(
                table_name=form_dic["form_table"]
            )
            form_model = Q2CursorModel(form_cursor)
            form.set_model(form_model)
            sql = f"select * from actions where form_name = '{form_name}' order by seq"
            cu = q2cursor(sql, self.db_logic)
            for x in cu.records():
                if x["action_mode"] == "1":
                    form.add_action("/crud")
                elif x["action_mode"] == "3":
                    form.add_action("-")
                else:
                    form.add_action(
                        x["action_text"],
                        self.code_runner(x["action_worker"])
                        if x["action_worker"]
                        else None,
                        child_form=lambda: self.get_form(x["child_form"]),
                        child_where=x["child_where"],
                        hotkey=x["action_key"],
                    )
        return form

    def code_error(self):
        return traceback.format_exc().replace("\n", "<br>").replace(" ", "&nbsp;")

    def code_compiler(self, script):
        script = script.replace("return", "pass;")
        try:
            code = compile(script, "'<worker>'", "exec")
            return {"code": code, "error": ""}
        except Exception:
            trace = self.code_error()
            return {
                "code": False,
                "error": f"""Compile error:<br><br>{trace}""",
            }

    def code_runner(self, script, form=None, __name__="__main__"):
        _form = form
        # to provide return ability for exec
        if "return " in script:
            nsl = []
            for x in script.split("\n"):
                if "return " in x:
                    if x.strip() == "return":
                        x = x.replace("return", "raise ReturnEvent")
                    else:
                        x = x.replace("return", "RETURN = ") + "; raise ReturnEvent"
                nsl.append(x)
            script = "\n".join(nsl)

        def real_runner():
            # make exec stop on return
            class ReturnEvent(Exception):
                pass

            __locals_dict = {
                "RETURN": None,
                "ReturnEvent": ReturnEvent,
                "mem": _form,
                "form": _form,
                "self": self,
                "q2_app": self,
                "__name__": __name__,
            }
            code = self.code_compiler(script)
            if code["code"]:
                try:
                    exec(code["code"], globals(), __locals_dict)
                except ReturnEvent:
                    pass
                except Exception:
                    trace = self.code_error()
                    q2Mess(f"""Runtime error:<br><br>{trace}""")
            else:
                q2Mess(code["error"])

            return __locals_dict["RETURN"]

        return real_runner

    def run_module(self, name=""):
        return self.code_runner(
            self.db_logic.get("modules", f"name = '{name}'", "script")
        )()


def main():
    app = Q2RadApp("q2RAD")
    app.dev_mode = 1
    app.run()


if __name__ == "__main__":
    main()
