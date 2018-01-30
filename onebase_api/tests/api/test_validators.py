#!/usr/bin/env python3
"""
This file is part of 1Base.

1Base is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

1Base is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with 1Base.  If not, see <http://www.gnu.org/licenses/>.
"""

import unittest
import logging
from json import dumps as ds
from faker import Faker
fake = Faker()

from onebase_api.tests.models.base import (
    CollectionUnitTest,
    global_setup,
    TEST_COLLECTION_NAME,
    fake,
    )

from onebase_api.models.main import (
    Type,
    Path,
    Node,
    Key,
    Slot,
)
from onebase_api import app

global_setup()
logger = logging.getLogger(__name__)

def _(u):
    return '/validate' + u

class TestValidators(unittest.TestCase):

    def verify_response(self, path, data, status):
        with app.app_context():
            client = app.test_client()
            resp = client.post(path, content_type='application/json',
                               data=ds(data))
            try:
                self.assertEqual(resp.status_code, status)
            except AssertionError as e:
                logger.error('path:     {}'.format(path))
                logger.error('data:     {}'.format(data))
                logger.error('status:   {}'.format(resp.status_code))
                logger.error('message:  {}'.format(resp.data))
                logger.error(e)
                raise e

    def do_fail_pass(self, path, pass_val, fail_val):
        with app.app_context():
            self.verify_response(path, pass_val, 200)
            self.verify_response(path, fail_val, 500)

    def test_int(self):
        logger.debug('Testing validator apps')
        for (k, v) in app.url_map._rules_by_endpoint.items():
            logger.debug("{} ||||| {}".format(k, v[0]))
        logger.debug('globals: {}'.format(app.view_functions))
        i = fake.pyint()
        self.do_fail_pass(_('/int'),
                          {'value': i, 'size': len(str(i))+1, },
                          {'value': i, 'size': len(str(i))-5, })
        self.do_fail_pass(_('/int'),
                          {'value': 0-i, 'size': len(str(0-i))+1, },
                          {'value': fake.pystr(), 'size': len(str(i))+5, })

    def test_str(self):
        s = fake.sentence(nb_words=10)
        self.do_fail_pass(_('/string'),
                          {'value': s, 'size': len(s)+1,},
                          {'value': s, 'size': len(s)-5})

    def test_float(self):
        f = fake.pyfloat()
        self.do_fail_pass(_('/float'),
                          {'value': f, 'size': len(str(f))+1, },
                          {'value': f, 'size': len(str(f))-5}, )
        self.do_fail_pass(_('/float'),
                          {'value': 0-f, 'size': len(str(0-f))+1, },
                          {'value': fake.pystr(), 'size': len(str(f))+5, })
