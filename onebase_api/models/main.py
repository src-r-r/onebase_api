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

from os.path import join

from odi_api.fields import (
    ForgivingURLField,
    SlugField,
    )
from odi_api.exceptions import OneBaseException
from mongoengine import (
    StringField,
    IntegerField,
    BooleanField,
    # ListField,
    ReferenceField,
    TextField,
    Document,
    DynamicField,
    DynamicDocument,
)
import requests

from odi_api.models.discussion import (
    # Discussion,
    DiscussionMixin,
)
from odi_api.models.mixin import (
    HistoricalMixin,
)


class Type(Document):
    """ Basic type for databases. """

    name = StringField(max_length=120)
    repr = ForgivingURLField()
    is_primitive = BooleanField(default=False)
    validator = ForgivingURLField()

    def validate_value(self, value, clean=False):
        """ Validate the value based on the type.

        :param value: Value to validate.

        :parm clean: Passed in from parent validate() method.

        :return: True on success, raise OneBaseException if invalid.

        """
        response = requests.post(self.validator, data=value)
        if response.status_code == 200:
            raise OneBaseException(response.json())
        return True


class Path(DiscussionMixin, HistoricalMixin, Document):
    """ Heirarchical organization of Node.

    Think of this like folders or directories on a filesystem.

    """

    parent = ReferenceField('Path')
    name = TextField(max_length=409, required=True, primary_key=True)

    def __str__(self):
        """ String representation of the Path. """
        if self.parent is None:
            return '/' + self.name
        return join(str(self.parent), self.name)

    @property
    def children(self):
        """ Child path elements. """
        Path.objects(parent=self)


class Node(DiscussionMixin, HistoricalMixin, Document):
    """ Equivalent to a table. Contains records for data.

    A Path may only have one Node, but several Paths pay lead to a Node. For
    example:

        /paint/warm/orange      --+
        /spectrum/lower/orange  --+--> Orange
    """

    name = SlugField(max_length=1024, primary_key=True)
    title = TextField(max_length=2048)
    description = TextField(max_length=4096)
    path = ReferenceField(Path, required=True)

    def full_path(self):
        """ Get the full path of the node. """
        return join(str(self.path), self.name)


class Key(DiscussionMixin, HistoricalMixin, DiscussionMixin, Document):
    """ Named slot within a node that contains values.

    Equivalent to an SQL column.
    """

    node = ReferenceField(Node)
    name = TextField(max_length=1024, required=True)
    comment = TextField(max_length=4096)
    soft_type = ReferenceField(Type)
    size = IntegerField(max_length=128)
    position = IntegerField(max_length=128)
    primary = BooleanField()


class Value(DynamicDocument, DiscussionMixin):
    """ Data value.

    Equivalent to a single cell in an SQL table.

    But what's unique about 1Base's values is that it's not constrained to
    basic types (here's looking at you, BLOB).

    Besides the normal primitives (INT, BOOL, etc.), a type can be anything,
    including multimedia, or even a reference to antoher table. Typically
    the value is represented by the `type.repr` URL.
    """

    key = ReferenceField(Key, required=True)
    row = IntegerField(max_length=128)
    value = DynamicField(required=True)

    def validate(self, clean=True):
        """ Validate this value.

        Validation is a bit unique for 1Base. We're calling a microservice
        (again) to verify the value is valid.
        """
        # Grab the validator
        self.key.soft_type.validate_value(self.value, clean)
