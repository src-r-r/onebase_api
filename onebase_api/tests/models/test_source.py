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
#
# from mongoengine.errors import (
#     ValidationError
# )

import unittest
import logging

from onebase_api.tests.models.base import (
    CollectionUnitTest,
    global_setup,
    TEST_COLLECTION_NAME,
    fake,
    )

from onebase_api.models.auth import (
    User,
    Group,
)

from onebase_api.models.source import (
    Source,
    # WebSource,
    # SourcedDocument,
)
from onebase_api.models.history import (
    Action,
)
from onebase_common.exceptions import OneBaseException

global_setup()

logger = logging.getLogger(__name__)


admin_group = Group(name='admin')
underpriv_group = Group(name='underprivileged', permissions=['none', ])
desktop_group = Group(name='desktop', permissions=['save_document', ])


def _get_test_user(group=admin_group):
    """ Get a test user. """
    u = User(email=fake.safe_email(), password=fake.password(),
             groups=[group, ])
    u.save()
    return u


class TestSource(CollectionUnitTest):
    """ Test the Source document. """

    database_name = TEST_COLLECTION_NAME

    def test_creation_without_user(self):
        """ Raise an exception if a source is created without a user. """
        with self.assertRaises(TypeError):
            source = Source(collection_method=Source.METHOD_MANUAL)
            source.save()

    def test_creation_with_user(self):
        """ A source w/ a user created; history added automatically. """
        u = _get_test_user()
        source = Source(collection_method=Source.METHOD_MANUAL)
        source.save(u)
        self.assertEqual(len(source.history), 1)
        self.assertEqual(source.history[0].event, Action.EVENT_CREATE)

    def test_permissions_saving(self):
        """ A user with proper permissions can save document. """
        adm_user = _get_test_user()
        und_user = _get_test_user(underpriv_group)
        desk_user = _get_test_user(desktop_group)
        source = Source(collection_method=Source.METHOD_MANUAL)
        source.save(adm_user)
        with self.assertRaises(OneBaseException):
            try:
                source.modify(description=fake.text(max_nb_chars=100))
                source.save(und_user)
            except OneBaseException as e:
                self.assertEqual(e.error_code, 'E-200')
                raise e
        # Don't raise an exception
        source.modify(description=fake.text(max_nb_chars=100))
        source.save(desk_user)
        self.assertEqual(len(source.history), 2)
        self.assertEqual(source.history[-1].user, desk_user)

    def test_source_modification(self):
        """ History contains 2 entries based on user. """
        u = _get_test_user()
        u2 = _get_test_user()  # just for kicks
        source = Source(collection_method=Source.METHOD_MANUAL)
        source.save(u)
        self.assertTrue(source.is_writable)
        self.assertFalse(source.is_readonly)
        self.assertEqual(len(source.history), 1)
        source.update(description=fake.text(max_nb_chars=100))
        source.save(u2)
        self.assertEqual(len(source.history), 2)
        self.assertEqual(source.history[-1].event, Action.EVENT_MODIFY)
        self.assertEqual(source.history[0].user, u)
        self.assertEqual(source.history[-1].user, u2)
        self.assertEqual(source.creator, u)

    @unittest.skip('')
    def test_source_hide(self):
        u = _get_test_user()
        source = Source(collection_method=Source.METHOD_MANUAL)
        source.save(u)
        self.assertEqual(source.is_visible, True)
        self.assertEqual(source.is_hidden, False)
        source.hide()
        source.save(u)
        self.assertEqual(source.is_visible, False)
        self.assertEqual(source.is_hidden, True)
        self.assertEqual(len(source.history), 2)
        source.show()
        source.save(u)
        self.assertEqual(source.is_visible, True)
        self.assertEqual(source.is_hidden, False)
        self.assertEqual(len(source.history), 3)


if __name__ == '__main__':
    unittest.main()
