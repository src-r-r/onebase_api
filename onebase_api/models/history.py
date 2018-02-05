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
    # URLField,
    StringField,
    DateTimeField,
    ListField,
    DynamicDocument,
    DynamicEmbeddedDocument,
)

from datetime import (
    datetime
)

from onebase_common.models.mixin import TimestampOrderableMixin


class Action(TimestampOrderableMixin, DynamicEmbeddedDocument):
    """ Modification, creation, or deletion of a Document.

    An item of history about a particular Document.
    """

    EVENT_CREATE = 'c'
    EVENT_MODIFY = 'm'
    EVENT_DELETE = 'd'  # NOTE: probably not used
    EVENT_READONLY = 'r'
    EVENT_WRITABLE = 'w'
    EVENT_HIDE = 'h'
    EVENT_SHOW = 's'

    EVENTS = (
        (EVENT_CREATE,      'Created'),
        (EVENT_MODIFY,      'Modified'),
        (EVENT_DELETE,      'Deleted'),  # probably not used
        (EVENT_READONLY,    'Mark Read-Only'),
        (EVENT_WRITABLE,    'Mark Writable'),
        (EVENT_HIDE,        'Hide'),
        (EVENT_SHOW,        'Show'),
    )

    user = ReferenceField('User', required=True)
    event = StringField(required=True, choices=EVENTS)
    timestamp = DateTimeField(required=True, default=datetime.now())
