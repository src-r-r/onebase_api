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

from faker import Faker
from pymongo import MongoClient
from mongoengine import connect
from onebase_common.log.setup import configure_logging

class CollectionUnitTest(unittest.TestCase):
    """ Adds functionality to tear down the database after test. """

    database_name = None

    def tearDown(self):
        """ Tear down the database. """
        logger = logging.getLogger(__name__)
        if self.database_name is None:
            raise AttributeError("Missing `database_name` property.")
        client = MongoClient()
        db = client[self.database_name]
        for cn in db.collection_names():
            logger.debug("dropping collection `{}`".format(cn))
            db.drop_collection(cn)


TEST_COLLECTION_NAME = 'test_oid_models_user'


def global_setup(collection_name=TEST_COLLECTION_NAME):
    """ Configure tests globally. """
    configure_logging()
    connect(collection_name)
    logger = logging.getLogger(__name__)
    return (logger, )


fake = Faker()
