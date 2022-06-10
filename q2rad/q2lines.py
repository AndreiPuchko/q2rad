if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2gui.q2model import Q2CursorModel
from q2rad.q2raddb import Q2Cursor, SeqMover

from q2rad import Q2Form

from q2gui import q2app


import gettext

_ = gettext.gettext

SQL_DATATYPES = (
    "char",
    "varchar",
    "text",
    "longtext",
    "num",
    "dec",
    "decimal",
    "date",
    "time",
    "datetime",
    "integer",
    "bigint",
    "int",
)
HAS_DATADEC = ("dec", "numeric", "num")
HAS_DATALEN = ("char", "varchar") + HAS_DATADEC
WIDGETS = ("line", "text", "code", "button", "check", "radio", "combo", "list", "spin")
# "date;"
# "frame;"
# "grid;"
# "label;"
# "lookup;"
# "progressbar;"
# "relation;"
# "space;"
# "tab;"
# "toolbar;"
# "toolbutton;"

HAS_PIC = "radio;" "combo;" "list;"


class Q2Lines(Q2Form, SeqMover):
    def __init__(self):
        super().__init__("Lines")
        self.db = q2app.q2_app.db_logic

    def on_init(self):
        self.create_form()

        cursor: Q2Cursor = self.q2_app.db_logic.table(table_name="lines", order="seq")
        model = Q2CursorModel(cursor)
        self.set_model(model)

        self.add_action("/crud")
        self.add_seq_actions()

        self.add_action("Run", self.form_runner, hotkey="F4")

    def create_form(self):
        self.add_control("id", "", datatype="int", pk="*", ai="*", noform=1, nogrid=1)
        self.add_control(
            "form_name",
            _("Form"),
            disabled="*",
            to_table="forms",
            to_column="form_name",
            related="title",
            nogrid=1,
            noform=1,
        )
        self.add_control("name", _("Column name"))
        self.add_control("/")
        if self.add_control("/t", _("Main")):
            self.add_control("/f")
            self.add_control("label", _("Form label"), datatype="char", datalen=100)
            self.add_control("gridlabel", _("Grid label"))
            if self.add_control("/h"):
                self.add_control("seq", _("Sequence number"), datatype="int")
                self.add_control("nogrid", _("No grid"), control="check")
                self.add_control("noform", _("No form"), control="check")
                self.add_control("check", _("Has checkbox"), control="check")
                self.add_control("/s")
                self.add_control("/")
            if self.add_control("/h", _("Control type")):

                def control_valid():
                    self.w.pic.set_enabled(self.s.control in HAS_PIC)

                self.add_control(
                    "control",
                    gridlabel=_("Control type"),
                    pic=";".join(WIDGETS),
                    control="combo",
                    valid=control_valid,
                    datatype="char",
                    datalen=15,
                )
                self.add_control("pic", _("Control data"), datatype="char", datalen=250)
                self.add_control("/")

            if self.add_control("/h", _("Data type")):

                def datatype_valid():
                    # print(self.crud_mode)
                    self.w.datalen.set_enabled(self.s.datatype in ";".join(HAS_DATALEN))
                    self.w.datadec.set_enabled(self.s.datatype in ";".join(HAS_DATADEC))

                self.add_control(
                    "datatype",
                    gridlabel=_("Data type"),
                    pic=";".join(SQL_DATATYPES),
                    control="combo",
                    valid=datatype_valid,
                    datatype="char",
                    datalen=15,
                )
                self.add_control("datalen", _("Data lenght"), datatype="int")
                self.add_control("datadec", _("Decimal lenght"), datatype="int")
                self.add_control("/s")
                self.add_control("/")

            if self.add_control("/h"):  # Db

                def database_valid():
                    # print(form.crud_mode)
                    self.w.pk.set_enabled(self.s.migrate)
                    self.w.ai.set_enabled(self.s.migrate)
                    # self.crud_mode
                    form_name = self.prev_form.r.form_name
                    id = self.r.id
                    id_where = ""
                    if self.crud_mode in ("EDIT", "VIEW"):
                        id_where = f" and id <> {id}"
                    sql = f"select * from lines where pk='*' and form_name = '{form_name}' {id_where}"
                    if not self.s.migrate or self.db.cursor(sql).row_count() > 0:
                        self.w.pk.set_disabled()
                        self.w.ai.set_disabled()

                self.add_control(
                    "migrate",
                    _("Migrate to database"),
                    control="check",
                    valid=database_valid,
                )
                self.add_control(
                    "pk",
                    _("Primary key"),
                    control="check",
                    valid=database_valid,
                )
                self.add_control(
                    "ai",
                    _("Autoincrement"),
                    control="check",
                    valid=database_valid,
                )
                self.add_control("/s")
                self.add_control("/")
            self.add_control("/")  # Linked
            if self.add_control("/f", _("Linked")):
                self.add_control(
                    "to_table", _("To table"), datatype="char", datalen=100
                )
                self.add_control(
                    "to_column", _("To field"), datatype="char", datalen=100
                )
                self.add_control(
                    "related", _("Data to show"), datatype="char", datalen=100
                )
                self.add_control(
                    "to_form", _("Form to open"), datatype="char", datalen=100
                )

                self.add_control("/")
            self.add_control("/s")

        self.add_control("/t", _("Comment"))
        self.add_control("comment", gridlabel=_("Comments"), datatype="bigtext")
        self.add_control("/t", _("Script When"))
        self.add_control(
            "code_when",
            _("Script When"),
            control="code",
            nogrid="*",
            datatype="bigtext",
        )
        self.add_control("/t", _("Script Show"))
        self.add_control(
            "code_show",
            _("Script When"),
            control="code",
            nogrid="*",
            datatype="bigtext",
        )
        self.add_control("/t", _("Script Valid"))
        self.add_control(
            "code_valid",
            _("Script When"),
            control="code",
            nogrid="*",
            datatype="bigtext",
        )

        def before_form_show():
            datatype_valid()
            control_valid()
            database_valid()

        self.before_form_show = before_form_show

        def before_crud_save():
            if not self.s.migrate:
                self.s.pk = ""
                self.s.ai = ""

        self.before_crud_save = before_crud_save

    def form_runner(self):
        self.prev_form.run_action("Run")
