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
    ListField,
    ReferenceField,
    SortedListField,
)

from odi_api.models.discussion import (
    Discussion,
)

class TimestampOrderableMixin(object):
    """ Class that contains a `timestamp` field.

    Overrides the comparison operators, so that the object can be sorted
    by date.
    """

    def __gt__(self, other):
        return self.timestamp > other.timestamp

    def __lt__(self, other):
        return self.timestamp < other.timestamp

    def __ge__(self, other):
        return self.timestamp >= other.timestamp

    def __le__(self, other):
        return self.timestamp <= other.timestamp

    def __eq__(self, other):
        return self.timestamp == other.timestamp

    def __ne__(self, other):
        return self.timestamp != other.timestamp

class DiscussionMixin(Document):
    """ Makes a document able to be discussed.

    Contains a refernce to discussions.

    """

    meta = {
        'abstract': True
    }

    discussions = ListField(ReferenceField(Discussion))


class HistoricalMixin(Document):
    """ Historical mixin class.

    Contains information on the Document being modified.

    """

    meta = {
        'abstract': True
    }

    history = SortedListField(ReferenceField(Action))
