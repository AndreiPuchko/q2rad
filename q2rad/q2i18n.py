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
from q2rad.q2utils import choice_table, choice_column, Q2_save_and_run, tr
from q2rad.q2utils import Q2Form

import ast
from typing import List, Tuple, Union, Optional


_ = tr


TranslatableItem = Union[
    Tuple[str, str],  # ("msgid", msgid)
    Tuple[str, str, str],  # ("msgctxt", context, msgid)
    Tuple[str, str, str, str],  # ("ngettext", singular, plural, msgid_plural)
]


def _const_str(node: ast.AST) -> Optional[str]:
    """Return string if node is a constant string or simple f-string."""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value

    if isinstance(node, ast.JoinedStr):
        # f-string: allow only if it contains no expressions
        parts = []
        for p in node.values:
            if isinstance(p, ast.Constant) and isinstance(p.value, str):
                parts.append(p.value)
            else:
                return None
        return "".join(parts)

    return None


def extract_translatable(code: str) -> List[TranslatableItem]:
    tree = ast.parse(code)

    out: List[TranslatableItem] = []

    class Visitor(ast.NodeVisitor):
        def visit_Call(self, node: ast.Call):
            # get function name like _("..") or gettext.gettext("..")
            func = node.func

            func_name = None
            module_name = None

            if isinstance(func, ast.Name):
                func_name = func.id
            elif isinstance(func, ast.Attribute):
                func_name = func.attr
                if isinstance(func.value, ast.Name):
                    module_name = func.value.id

            # handle _("..")
            if func_name == "_":
                if node.args:
                    msgid = _const_str(node.args[0])
                    if msgid is not None:
                        out.append(("msgid", msgid))

            # handle gettext.gettext("..")
            elif func_name == "gettext" and module_name == "gettext":
                if node.args:
                    msgid = _const_str(node.args[0])
                    if msgid is not None:
                        out.append(("msgid", msgid))

            # handle pgettext(ctx, msg)
            elif func_name == "pgettext":
                if len(node.args) >= 2:
                    ctx = _const_str(node.args[0])
                    msgid = _const_str(node.args[1])
                    if ctx is not None and msgid is not None:
                        out.append(("msgctxt", ctx, msgid))

            # handle gettext.pgettext(ctx, msg)
            elif func_name == "pgettext" and module_name == "gettext":
                if len(node.args) >= 2:
                    ctx = _const_str(node.args[0])
                    msgid = _const_str(node.args[1])
                    if ctx is not None and msgid is not None:
                        out.append(("msgctxt", ctx, msgid))

            # handle ngettext(singular, plural, n)
            elif func_name == "ngettext":
                if len(node.args) >= 2:
                    singular = _const_str(node.args[0])
                    plural = _const_str(node.args[1])
                    if singular is not None and plural is not None:
                        out.append(("ngettext", singular, plural, plural))

            # handle gettext.ngettext
            elif func_name == "ngettext" and module_name == "gettext":
                if len(node.args) >= 2:
                    singular = _const_str(node.args[0])
                    plural = _const_str(node.args[1])
                    if singular is not None and plural is not None:
                        out.append(("ngettext", singular, plural, plural))

            self.generic_visit(node)

    Visitor().visit(tree)
    return out


class Q2Locale(Q2Form):
    def __init__(self, title=_("Locale")):
        super().__init__(title)
        self.no_view_action = True

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

    def create_form(self):
        self.add_control("lang", _("Language"), datatype="char", datalen=10, pk="*")
        self.add_control("name", _("Name (English)"), datatype="char", datalen=100)
        self.add_control("native_name", _("Native name"), datatype="char", datalen=100)
        self.add_control("enabled", _("Enabled"), datatype="char", datalen=1, control="check")

    def collect(self):
        sql = """
select *
from(
        select title as msgid from forms
union select menu_path from forms 
union select menu_text from forms 
union select menu_before from forms 
union select menu_tiptext from forms 

union select label from `lines`
union select gridlabel from `lines`
union select mess from `lines`


union select action_text from actions
union select action_mess from actions
) qq
where msgid<>""
order by 1
        """
        locales = [x["lang"] for x in q2cursor("select lang from locale", q2app.q2_app.db_logic).records()]
        for rec in q2cursor(sql, q2app.q2_app.db_logic).records():
            for lang in locales:
                rec["lang"] = lang
                msgid = rec["msgid"]
                ensure_record(
                    table_name="locale_po",
                    where=f"msgid='{msgid}' and lang='{lang}'",
                    record=rec,
                    q2_db=q2app.q2_app.db_logic,
                )
        sql_code = """
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

) qq
where msgid<>""
order by 1
        """
        # for x in q2cursor(sql_code, q2app.q2_app.db_logic).records():
        #     print(extract_translatable(x["msgid"]))
        # self.refresh()


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
        self.add_control("id", "", datatype="int", pk="*", ai="*")
        self.add_control("lang", _("Language"), datatype="char", datalen=10, disabled=1)
        self.add_control("context", _("Context"), datatype="char", datalen=100, disabled=1)
        self.add_control("msgid", _("Key"), datatype="char", datalen=255, disabled=1)
        self.add_control("msgstr", _("Translation"), datatype="text")
