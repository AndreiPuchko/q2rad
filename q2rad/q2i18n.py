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


from q2db.cursor import Q2Cursor

from q2gui.q2model import Q2CursorModel

from q2gui.q2dialogs import q2mess, q2ask
from q2gui import q2app
from q2rad.q2utils import q2cursor
from q2rad.q2raddb import ensure_record, last_error

from q2rad.q2lines import Q2Lines
from q2rad.q2actions import Q2Actions
from q2rad.q2utils import choice_table, choice_column, Q2_save_and_run, tr, clear_i18n_cache
from q2rad.q2utils import Q2Form

import ast

_ = tr


forms_translate = ["title", "menu_path", "menu_text", "menu_before", "menu_tiptext"]
lines_translate = ["label", "gridlabel", "mess"]
actions_translate = ["action_text", "action_mess"]

forms_sql = " union ".join([f"select {x} as msgid from forms" for x in forms_translate])
lines_sql = " union ".join([f"select {x} as msgid from `lines`" for x in lines_translate])
actions_sql = " union ".join([f"select {x} as msgid from actions" for x in actions_translate])

collect_strings_sql = f"""
select *
from( {forms_sql} union {lines_sql} union {actions_sql} ) qq
where msgid<>""
order by 1
"""

collect_code_sql = """
select *
from(
    select after_form_load as msgid from forms
union select before_form_build from forms 
union select before_grid_build from forms 
union select before_grid_show from forms 
union select after_grid_show from forms 
union select before_form_show from forms 
union select after_form_show from forms 
union select before_crud_save from forms 
union select after_crud_save from forms 
union select before_delete from forms 
union select after_delete from forms 
union select form_valid from forms 
union select form_refresh from forms 
union select after_form_closed from forms 

union select code_when from `lines`
union select code_show from `lines`
union select code_valid from `lines`

union select action_worker from actions

union select script from modules

) qq
where msgid<>""
order by 1
"""


def extract_translatable(code: str) -> list[dict]:
    def _const_str(node: ast.AST) -> str:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value

        if isinstance(node, ast.JoinedStr):
            parts = []
            for p in node.values:
                if isinstance(p, ast.Constant) and isinstance(p.value, str):
                    parts.append(p.value)
                else:
                    return ""
            return "".join(parts)

        return ""

    tree = ast.parse(code)
    out: list[dict] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            func = node.func

            name = None
            # module = None

            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
                # if isinstance(func.value, ast.Name):
                #     module = func.value.id

            # _("msg")
            if name == "_":
                if node.args:
                    if msgid := _const_str(node.args[0]):
                        out.append(
                            {
                                "msgid": msgid,
                                "msgctxt": "",
                                "plural": "",
                            }
                        )

            # pgettext(ctx, msg)
            elif name == "pgettext":
                if len(node.args) >= 2:
                    ctx = _const_str(node.args[0])
                    msgid = _const_str(node.args[1])
                    if ctx and msgid:
                        out.append(
                            {
                                "msgid": msgid,
                                "msgctxt": ctx,
                                "plural": "",
                            }
                        )

            # ngettext(s, p, n)
            elif name == "ngettext":
                if len(node.args) >= 2:
                    s = _const_str(node.args[0])
                    p = _const_str(node.args[1])
                    if s and p:
                        out.append(
                            {
                                "msgid": s,
                                "msgctxt": "",
                                "plural": p,
                            }
                        )

            self.generic_visit(node)

    Visitor().visit(tree)
    return out


def get_tranlations():
    langs = [{"lang": "en", "name": "English", "native_name": ""}]
    for lang in q2cursor(
        "select * from locale where disabled=''", q2_db=q2app.q2app.q2_app.db_logic
    ).records():
        langs.append(lang)
    return langs


class Q2Locale(Q2Form):
    def __init__(self, title=_("Locale")):
        super().__init__(title)
        self.no_view_action = True
        self.locales = []

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="locale", order="lang")
        model = Q2CursorModel(cursor)
        self.set_model(model)

        self.add_action("/crud")

        self.add_action(
            _("Translations"),
            child_form=Q2LocalePo,
            child_where="lang='{lang}'",
            hotkey="F2",
            eof_disabled=1,
        )
        self.add_action(
            _("Collect"),
            self.collect,
            hotkey="F4",
            eof_disabled=1,
        )
        self.add_action(
            _("Clear cache"),
            self.clear_cache,
            eof_disabled=1,
        )

    def clear_cache(self):
        clear_i18n_cache()

    def create_form(self):
        self.add_control("lang", _("Language"), datatype="char", datalen=10, pk="*")
        self.add_control("name", _("Name (English)"), datatype="char", datalen=100)
        self.add_control("native_name", _("Native name"), datatype="char", datalen=100)
        self.add_control("disabled", _("Disabled"), datatype="char", datalen=1, control="check")

    def collect(self):
        self.locales = [
            x["lang"] for x in q2cursor("select lang from locale", q2app.q2_app.db_logic).records()
        ]
        for rec in q2cursor(collect_strings_sql, q2app.q2_app.db_logic).browse().records():
            self.add_msg(rec)
        for x in q2cursor(collect_code_sql, q2app.q2_app.db_logic).records():
            words = extract_translatable(q2app.q2_app.code_compiler(x["msgid"])["script"])
            for rec in words:
                self.add_msg(rec)
        self.refresh()

    def add_msg(self, rec):
        for lang in self.locales:
            rec["lang"] = lang
            msgid = rec["msgid"]
            ensure_record(
                table_name="locale_po",
                where=f"msgid='{msgid}' and lang='{lang}'",
                record=rec,
                q2_db=q2app.q2_app.db_logic,
            )


class Q2LocalePo(Q2Form):
    def __init__(self, title=_("Tranlations")):
        super().__init__(title)
        self.no_view_action = True

    def on_init(self):
        self.create_form()
        self.db = q2app.q2_app.db_logic
        cursor: Q2Cursor = self.db.table(table_name="locale_po", order="msgid")
        model = Q2CursorModel(cursor)
        self.set_model(model)

        self.add_action("/crud")

    def create_form(self):
        self.add_control("id", "", datatype="int", pk="*", ai="*", nogrid=1, noform=1)
        self.add_control("lang", _("Language"), datatype="char", datalen=10, disabled=1)
        self.add_control("msgid", _("Key"), datatype="char", datalen=255, disabled=1)
        self.add_control("msgstr", _("Translation"), datatype="text")
        self.add_control("context", _("Context"), datatype="char", datalen=100, disabled=1)
