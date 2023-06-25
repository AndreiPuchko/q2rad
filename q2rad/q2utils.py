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

import sys
import os
import random
import string
import threading


if __name__ == "__main__":

    sys.path.insert(0, ".")
    from q2rad.q2rad import main

    main()

from q2rad import Q2Form
from q2rad.q2raddb import q2cursor
from q2gui.q2model import Q2Model
from q2gui import q2app
from q2gui.q2dialogs import q2working
import logging
from logging.handlers import TimedRotatingFileHandler

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


def set_logging(log_folder="log"):
    if not os.path.isdir(log_folder):
        os.mkdir(log_folder)
    handler = TimedRotatingFileHandler(f"{log_folder}/q2.log", when="midnight", interval=1, backupCount=5)
    formatter = logging.Formatter("%(asctime)s-%(name)s: %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logging.basicConfig(handlers=[handler])


class Q2Logger:
    def __init__(self, log_folder="log"):
        # self.sys_stderr = sys.stderr
        self.buffer = ""
        if not os.path.isdir(log_folder):
            os.mkdir(log_folder)
        handler = TimedRotatingFileHandler(f"{log_folder}/q2.log", when="midnight", interval=1, backupCount=5)
        formatter = logging.Formatter("%(asctime)s-%(name)s: %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logging.basicConfig(handlers=[handler])
        # sys.stderr = self

    def write(self, message):
        if message:
            self.buffer += message
        sys.stdout.write(message)

    def flush(self):
        if self.buffer.strip():
            logging.error(self.buffer)
        sys.stdout.flush()
        self.buffer = ""


class Q2Tasker:
    def __init__(self, title="Working..."):
        self.rez = {}
        self.threads = {}
        self.title = title

    def _worker(self, name):
        self.rez[name] = self.threads[name]["worker"](*self.threads[name]["args"])

    def add(self, worker, *args, name=""):
        if name == "" or name in self.threads:
            name = "".join(
                random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(5)
            )
        self.threads[name] = {"worker": worker, "args": args}
        self.threads[name]["thread"] = threading.Thread(target=self._worker, args=(name,))
        self.threads[name]["thread"].start()

    def wait(self):
        def _wait(self=self):
            for name in self.threads:
                self.threads[name]["thread"].join()

        q2working(_wait, self.title)
        return self.rez
