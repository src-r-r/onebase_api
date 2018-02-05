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

# import unittest
import logging
import unittest

from mongoengine import *

from onebase_api.models.auth import (
    User,
    Group,
)
from onebase_api.models.main import (
    Type,
    Key,
    Path,
    Node,
    create_node_at_path,
)

from onebase_api.tests.models.base import (
    CollectionUnitTest,
    global_setup,
    TEST_COLLECTION_NAME,
    fake,
    )
from onebase_common.log.setup import configure_logging
from onebase_common.exceptions import OneBaseException

configure_logging()
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

class TestTypes(AccountTestMixin):

    database_name = 'test_type'

    def _base(self, u):
        return 'http://localhost:5002' + u

    def test_creation(self):
        int_type = Type(name='INTEGER',
                        validator=self._base('/validate/int'),
                        repr=self._base('/repr/int'))
        int_type.save()
        i = Type.objects(name='INTEGER').first()
        self.assertIsNotNone(i)

    def test_validation(self):
        int_type = Type(name='INTEGER2',
                        validator=self._base('/validate/int'),
                        repr=self._base('/repr/int'))
        int_type.save()
        i = Type.objects(name='INTEGER2').first()
        self.assertTrue(i.validate_value('100', 5))
        try:
            i.validate_value('something', 10)
            raise AssertionError()
        except OneBaseException as e:
            self.assertEqual(e.error_code, 'E-101')

class TestKeys(AccountTestMixin):

    database_name = 'test_keys'
    _base = 'validator/{}'.format

    def setUp(self):
        super(TestKeys, self).setUp()
        int_type = Type(name='INTEGER',
                        validator=self._base('/validate/int'),
                        repr=self._base('/repr/int'))
        int_type.save()
        self.int_type = int_type

    def test_key_creation(self):
        key = Key(name=fake.word(),
                  soft_type=self.int_type,
                  comment=fake.sentence(),
                  size=1024)
        key.save(self.admin)
        self.assertIsNotNone(Key.objects.first())

class TestPath(AccountTestMixin):

    database_name = 'test_path'

    def test_create(self):
        """ Root element can be created. """
        path = Path.create(self.admin, '/root')
        path.save(self.admin)
        self.assertEqual(Path.objects.count(), 1)
        self.assertIsNotNone(Path.objects(name='root').first())

    def test_create_hierarchy(self):
        """ A complete path can be created. """
        Path.objects.delete()
        path = Path.create(self.admin, '/root2/a')
        path.save(self.admin)
        path = Path.create(self.admin, '/root2/b')
        path.save(self.admin)
        for p in Path.objects.all():
            logger.debug('Created path: {}'.format(p))
        self.assertEqual(Path.objects.count(), 3)
        self.assertEqual(len(Path.find('/root2').paths), 2)

    def test_nocreate_redundant(self):
        """ If a path already exists, an exception will be raised. """
        Path.objects.delete()
        wrds = fake.words(nb=5)
        pathstr = '/' + '/'.join(wrds)
        Path.create(self.admin, pathstr)
        try:
            Path.create(self.admin, pathstr)
            self.assertFalse(True)
        except OneBaseException as e:
            self.assertEqual(e.error_code, 'E-206')

    def test_nocreate_parent_redundant(self):
        """ A parented path cannot be created. """
        Path.objects.delete()
        wrds = fake.words(nb=5)
        pathstr = '/' + '/'.join(wrds)
        Path.create(self.admin, pathstr)
        try:
            pathstr = '/' + '/'.join(wrds[:-1])
            Path.create(self.admin, pathstr)
            self.assertFalse(True)
        except OneBaseException as e:
            self.assertEqual(e.error_code, 'E-206')


class TestNode(AccountTestMixin):
    """ Node tests. """

    @unittest.skip('later')
    def test_node_view(self):
        """ A node can be viewed. """
        def _base(u):
            return 'http://localhost:5002' + u
        types = {
            'integer': Type(name='INTEGER',
                            validator=_base('/api/1.0/validate/int'),
                            repr=_base('/api/1.0/repr/int'),
                            )
        }
        for t in types:
            t.save()
        keys = [
            Key(name='first', type=types['integer'])
        ]
        node = Node()
        path = create_node_at_path(self.admin, '/root/a/b', node)
