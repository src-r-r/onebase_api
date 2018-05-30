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
    Path,
    Node,
    Key,
    Slot,
)
from onebase_api.models.auth import (
    User,
    Group,
)
from onebase_api.models.types import (
    TYPE_SELECTION,
    IntegerType,
    StringType,
    ColorType,
    )

from onebase_api import app
from onebase_api.api.doc import prepend_url as _

global_setup()
logger = logging.getLogger(__name__)


class AccountTestMixin(CollectionUnitTest):

    def setUp(self):
        e = fake.safe_email()
        group = Group.objects(name='admin').first()
        if group is None:
            group = Group(name='admin')
            group.save()
        self.admin = User.objects(email=e).first()
        if self.admin is None:
            self.admin = User(email=e,
                              groups=[group, ],
                              password=fake.password(length=16))
            self.admin.save()

class TestIntType(AccountTestMixin):

    database_name='onebase_test_int_type'

    def setUp(self):
        super(TestIntType, self).setUp()
        self.user = self.admin
        key = Key(name=fake.word(),
                  soft_type='INTEGER',
                  size=1024)
        key.save(self.user)
        self.valid_slots = (
            Slot(key=key, value=fake.pyint()),
            Slot(key=key, value=str(0-fake.pyint())),
            Slot(key=key, value='+' + str(fake.pyint())),
            )
        for s in self.valid_slots:
            s.save(self.user)
        self.invalid_slots = (
            Slot(key=key, value='123.456'),
            Slot(key=key, value={'dictionary': 1}),
        )
        for s in self.invalid_slots:
            s.save(self.user)

    def test_validation(self):
        for (i, v) in enumerate(self.valid_slots):
            logger.debug("Testing self.valid_slots[{}]".format(i))
            self.assertTrue(v.validate())
        for (i, v) in enumerate(self.invalid_slots):
            logger.debug("Testing self.invalid_slots[{}]".format(i))
            self.assertFalse(v.validate())

    def test_prepare(self):
        """ Integer requires no preparation. """
        key = Key(name=fake.word(),
                  soft_type='INTEGER',
                  size=1024)
        key.save(self.user)
        slot = Slot(key=key, value=fake.pyint())
        slot.save(self.user)
        prepared = slot.prepare()
        self.assertEqual(int(prepared), slot.value)

    def test_get_attrs(self):
        key = Key(name=fake.word(),
                  soft_type='INTEGER',
                  size=1024)
        key.save(self.user)
        slot = Slot(key=key, value=fake.pyint())
        slot.save(self.user)
        attrs = slot.get_attrs()
        self.assertEqual(attrs.get('type'), 'text/plain')

    def test_render(self):
        key = Key(name=fake.word(),
                  soft_type='INTEGER',
                  size=1024)
        key.save(self.user)
        slot = Slot(key=key, value=fake.pyint())
        slot.save(self.user)
        resp = slot.render()
        self.assertEqual(resp, str(slot.value))

    def test_api_respond(self):
        """ API responds correctly. """
        client = app.test_client()
        key = Key(name=fake.word(),
                  soft_type='INTEGER',
                  size=1024)
        key.save(self.user)
        slot = Slot(key=key, value=fake.pyint())
        slot.save(self.user)
        resp = client.get('/slot/render/{}'.format(slot.id))
        logger.debug('test_api_response body={}'.format(resp.data))
        self.assertEqual(resp.data, str(slot.value))
        self.assertEqual(resp.status_code, 200)
