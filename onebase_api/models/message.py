#!/usr/bin/env python3

"""
This file is part of 1Base.

Foobar is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Foobar is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with 1Base.  If not, see <http://www.gnu.org/licenses/>.
"""

import logging

from datetime import (
    datetime
)

from mongoengine import (
    Document,
    StringField,
    ListField,
    EmailField,
    ReferenceField,
    DateTimeField,
    BooleanField,
)

from onebase_api.models.auth import (
    User,
)

class PrivateMessage(Document)
    """ TODO: Incorporate OpenPGP encryption for **secure** messaging. """

    sender = ReferenceField(User, required=True)
    recipient = ReferenceField(User, required=True)
    sent = DateTimeField(default=datetime.now(), required=True)
    read = DateTimeField(default=datetime.now(), required=True)
    is_draft = BooleanField(default=True)

    subject = StringField(max_length=1024)
    body = StringField(required=True)
