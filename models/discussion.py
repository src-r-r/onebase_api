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

from mongoengine import (
    Document,
    ReferenceField,
    BooleanField,
    TextField,
    DateTimeField,
    ListField
)

from odi_api.models.mixin import (
    TimestampOrderableMixin
)


class Comment(TimestampOrderableMixin, Document):
    """ A part of a discussion. """

    author = ReferenceField('User', required=True)
    timestamp = DateTimeField(required=True)
    body = TextField(max_lenth=4096, required=True)
    replies = ListField(ReferenceField('Comment'))


class Discussion(Document):
    """ User comments pertaining to a part of 1Base.

    As with any wiki, a disagreement may arise. Discussions are there to
    allow users to state ther opinion on a particular issue.

    """

    title = TextField()
    comments = ListField(ReferenceField(Comment))
    is_locked = BooleanField()

    meta = {'allow_inheritance': True, }

    @property
    def starter(self):
        """ Return the user that started the discussion. """
        self.comments[0].author
