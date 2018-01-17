#!/usr/bin/env python3

import csv

from odi_common.settings import (
    ERRORS_FILE
)

def load_errors():
    errors = {}
    with open(ERRORS_FILE) as errors_file:
        reader = csv.reader(errors_file)
        for row in reader:
            errors[row[0]] = row[1]
    return errors

class OneBaseException(Exception):

    def __init__(error_code, **format_args):
        self.error_code = error_code
        self.format_args = format_args

    def __repr__(self):
        e = load_errors()
        return e[str(self.error_code)].format(**self.format_args)
