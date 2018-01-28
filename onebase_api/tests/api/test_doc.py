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
from json import (dumps as ds, loads as ls)
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
from onebase_api.api.doc import prepend_url as _

global_setup()
logger = logging.getLogger(__name__)

class TestDoc(unittest.TestCase):

    def test_index(self):
        with app.app_context():
            client = app.test_client()
            resp = client.get(_('/'))
            logger.debug('THIS IS...THE DOCUMENTATION: {}'.format(resp.data))
            d = ls(resp.data.decode('ascii'))
            self.assertEqual(resp.status_code, 200)
            self.assertGreater(len(d['data'].keys()), 0)
