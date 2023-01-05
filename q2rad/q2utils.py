if __name__ == "__main__":
    import sys

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2rad import Q2Form
from q2rad.q2raddb import q2cursor
from q2gui.q2model import Q2Model
from q2gui import q2app

import gettext

_ = gettext.gettext


def q2choice(records=[], title="Make your choice", column_title="Column"):
    setta = Q2Form(title)
    column = list(records[0].keys())[0]
    setta.add_control(column, column_title)
    setta.no_view_action = 1
    model = Q2Model()
    # model.set_records(
    #     [{"table": x} for x in self.q2_app.db_data.db_schema.get_schema_tables()]
    # )
    model.set_records(records)

    setta.set_model(model)
    setta.heap.selected = None

    def make_choice():
        setta.heap.selected = setta.r.__getattr__(column)
        setta.close()

    setta.add_action(
        _("Select"),
        make_choice,
        hotkey="Enter",
        tag="select",
        eof_disabled=1,
    )
    setta.run()
    return setta.heap.selected


def choice_table():
    return q2choice(
        [{"table": x} for x in q2app.q2_app.db_data.db_schema.get_schema_tables()],
        title="Select table",
        column_title="Table",
    )


def choice_column(table):
    return q2choice(
        [{"col": x} for x in q2app.q2_app.db_data.db_schema.get_schema_columns(table)],
        title="Select column",
        column_title="Column",
    )


def choice_form():
    return q2choice(
        [
            x
            for x in q2cursor(
                """
                select name
                from forms
                order by name
                """,
                q2app.q2_app.db_logic,
            ).records()
        ],
        title="Select form",
        column_title="Form name",
    )
