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
    StringField,
    ListField,
    EmailField,
    ReferenceField,
)


class Group(Document):
    """ Collection of users with certain permissions. """

    name = StringField(primary_key=True)
    permissions = ListField(StringField(max_length=1024))


class User(Document):
    """ An account on 1base. """

    email = EmailField(max_length=1024, required=True, unique=True)
    password = StringField(max_length=1027, required=True)
    username = StringField(max_length=120, required=False, unique=True)
    groups = ListField(ReferenceField(Group))
