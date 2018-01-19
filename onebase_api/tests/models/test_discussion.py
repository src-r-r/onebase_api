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

from mongoengine.errors import (
    ValidationError
)

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
from onebase_api.models.discussion import (
    DeletedComment,
    Comment,
    Discussion,
)

global_setup()

logger = logging.getLogger(__name__)

def _get_test_user():
    u = User(email=fake.safe_email(), password=fake.password())
    u.save()
    return u


def _get_test_comment(author=_get_test_user()):
    author.save()
    c = Comment(author=author, body=fake.paragraph())
    c.save()
    return c


class TestComment(unittest.TestCase):
    """ test cases for the Comment object. """

    def test_create(self):
        """ Comment can be created. """
        u = _get_test_user()
        u.save()
        comment = Comment(author=u, body=fake.paragraph())
        comment.save()
        self.assertGreater(len(Comment.objects), 0)

    def test_create_tree(self):
        """ Comment can be heirarchical. """
        u = _get_test_user()
        comment = Comment(author=u, body=fake.paragraph())
        comment.save()
        replies = (
            _get_test_comment(),
            _get_test_comment(),
        )
        [comment.replies.append(c) for c in replies]
        comment.save()
        # Assure the heirarchy is correct.
        logger.info("Comment: {}".format(comment))
        self.assertEqual(replies[0].parent, comment)
        self.assertEqual(replies[1].parent, comment)
        self.assertEqual(len(comment.replies), 2)
        for c in replies:
            self.assertIn(c, comment.replies)
        # now try a 2nd level!
        another_reply = _get_test_comment()
        replies[0].replies.append(another_reply)
        replies[0].save()
        self.assertEqual(len(comment.replies[0].replies), 1)

    def test_delete_comment(self):
        """ No ill effects if a comment is deleted. """
        root = _get_test_comment()
        r = _get_test_comment()
        r.replies.append(_get_test_comment())
        r.replies.append(_get_test_comment())
        r.save()
        root.replies.append(r)
        root.replies.append(_get_test_comment())
        root.replies.append(_get_test_comment())
        root.save()
        comment_count = Comment.objects.count()
        logger.debug('test: deleting root {}'.format(root.id))
        root.delete()
        self.assertEqual(len(Comment.objects),  comment_count-1)
        if r.parent is not None:
            print("test object parent {}".format(r.parent))
        self.assertEqual(type(r.parent), DeletedComment)


class TestDiscussion(unittest.TestCase):
    """ Test the Discussion object. """

    def test_creation(self):
        """ Discussion can be created. """
        comments = (
            _get_test_comment(),
            _get_test_comment(),
        )
        discussion = Discussion(title=fake.text(max_nb_chars=30),
                                comments=comments)
        discussion.save()
        logger.debug("Discussion: {}".format(discussion))
        for c in comments:
            self.assertIn(c, discussion.comments)
        self.assertEqual(discussion.starter, comments[0])

    def test_creation_without_comment(self):
        """ An error occurs if a discussion is created without a comment. """
        d = Discussion(title=fake.text(max_nb_chars=1024))
        with self.assertRaises(ValidationError):
            d.save()


if __name__ == '__main__':
    global_setup()
    unittest.main()
