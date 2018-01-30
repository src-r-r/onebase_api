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

from mongoengine import *

from onebase_api.models.auth import (
    User,
    Group,
)
from onebase_api.models.main import (
    Path,
    Node,
)

from onebase_api.tests.models.base import (
    CollectionUnitTest,
    global_setup,
    TEST_COLLECTION_NAME,
    fake,
    )
from onebase_common.log.setup import configure_logging
from onebase_api.exceptions import OneBaseException

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
