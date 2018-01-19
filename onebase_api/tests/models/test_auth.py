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

from mongoengine import *

from onebase_api.models.auth import (
    User,
    Group,
)

from onebase_api.tests.models.base import (
    CollectionUnitTest,
    global_setup,
    TEST_COLLECTION_NAME,
    fake,
    )
from onebase_common.log.setup import configure_logging

configure_logging()
global_setup()

logger = logging.getLogger(__name__)


class TestUser(CollectionUnitTest):
    """ User functionality. """

    database_name = TEST_COLLECTION_NAME

    def test_user_create(self):
        """ User can be created. """
        user = User(email=fake.safe_email(), password=fake.password())
        user.save()
        self.assertGreater(len(User.objects), 0)


class TestGroup(CollectionUnitTest):
    """ Group functionality. """

    database_name = TEST_COLLECTION_NAME

    def test_add_user(self):
        """ User can be added to a group; can be listed from Group.users. """
        user = User(email=fake.safe_email(), password=fake.password())
        user.save()
        group_a = Group(name='group_a', permissions=['create_post', ])
        group_a.save()
        group_b = Group(name='group_b', permissions=['delete_post', ])
        group_b.save()
        user.groups.append(group_a)
        user.save()
        self.assertTrue(group_a in user.groups)
        group_a_users = group_a.users
        self.assertIn(user, group_a_users)
        self.assertNotIn(user, group_b.users)
        logger.info('User: {}'.format(user))
        logger.info('Group: {}'.format(group_a))

    def test_permissions(self):
        """ Permission configured correctly. """
        group_admin = Group(name='admin')
        group_desktop = Group(name='desktop', permissions=['p1', ])
        group_other = Group(name='another', permissions=['p2', ])
        # group_under = Group(name='underprivileged')

        admin = User(email=fake.safe_email(), password=fake.password(),
                     groups=[group_admin, ])
        admin.save()
        desktop = User(email=fake.safe_email(), password=fake.password(),
                       groups=[group_desktop, group_other, ])
        desktop.save()
        user = User(email=fake.safe_email(), password=fake.password())
        user.save()

        self.assertTrue(admin.is_admin)
        self.assertFalse(desktop.is_admin)
        self.assertFalse(user.is_admin)

        self.assertListEqual(desktop.all_permissions, ['p1', 'p2'])

        self.assertTrue(admin.can_any('something', 'another_thing'))
        self.assertTrue(admin.can_all('something', 'another_thing'))
        self.assertTrue(desktop.can_all('p1', 'p2'))
        self.assertTrue(desktop.can_any('p1', 'run_marathon'))
        self.assertFalse(desktop.can_any('save_the_world', 'run_marathon'))
        self.assertFalse(user.can_any('p1', 'p2', 'p3'))
        self.assertFalse(user.can_any())


if __name__ == '__main__':
    unittest.main()
