#!/usr/bin/env python3

import csv
import logging

from onebase_common.settings import (
    ERRORS_FILE
)

from onebase_common.log.setup import configure_logging

logger = logging.getLogger(__name__)

def load_errors():
    errors = {}
    logger.debug('...loading errors...')
    with open(ERRORS_FILE) as errors_file:
        reader = csv.reader(errors_file)
        for row in reader:
            # logger.debug('{} - {}...'.format(row[0], row[1][:10]))
            errors[row[0]] = row[1]
    return errors

class OneBaseException(Exception):

    def __init__(self, error_code, **format_args):
        self.error_code = error_code
        self.format_args = format_args

    def __str__(self):
        e = load_errors()
        k = str(self.error_code)
        # logger.debug('format_args: {}'.format(self.format_args))
        # return k
        return e[k].format(**self.format_args)

    def __repr__(self):
        return str(self)

    def __unicode__(self):
        return srt(self)
