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
from onebase_api.api import app
from onebase_api.api.validators import prepend_url as _

global_setup()
logger = logging.getLogger(__name__)


class TestValidators(unittest.TestCase):

    def test_int(self):
        with app.app_context():
            client = app.test_client()
            resp = client.post(_('/int'),
                               content_type='application/json',
                               data={'value': 1024, })
        logger.debug(resp.response)
        self.assertEqual(resp.status_code, 200)
