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

from pymongo import MongoClient
from mongoengine import *
from faker import Faker

from odi_api.models.auth import *
from odi_common.log.setup import configure_logging

TEST_COLLECTION_NAME = 'test_oid_models_user'

# Connect for mongoengine
connect(TEST_COLLECTION_NAME)

fake = Faker()


configure_logging()
logger = logging.getLogger(__name__)


class CollectionUnitTest(unittest.TestCase):

    database_name = None

    def tearDown(self):
        client = MongoClient()
        db = client[self.database_name]
        for cn in db.collection_names():
            logger.debug("dropping collection `{}`".format(cn))
            db.drop_collection(cn)


class TestUser(unittest.TestCase):

    database_name = TEST_COLLECTION_NAME

    def test_user_create(self):
        """ User can be created. """
        user = User(email=fake.safe_email(), password=fake.password())
        user.save()
        self.assertGreater(len(User.objects), 0)


if __name__ == '__main__':
    unittest.main()
