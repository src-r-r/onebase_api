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

import logging

from os.path import join

from onebase_api.fields import (
    ForgivingURLField,
    SlugField,
    )
from onebase_api.exceptions import OneBaseException
from mongoengine import (
    StringField,
    IntField as IntegerField,
    BooleanField,
    ListField,
    ReferenceField,
    Document,
    DynamicField,
    DynamicDocument,
)
import requests

from onebase_api.models.mixin import (
    HistoricalMixin,
    DiscussionMixin,
)
from onebase_common.util import (
    path_split,
    path_head_tail,
)

logger = logging.getLogger(__name__)


class Type(Document):
    """ Basic type for databases. """

    name = StringField(max_length=120, unique=True)
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

    @classmethod
    def as_select(cls):
        """ Convenience method for getting a select-style list. """
        return [(t.id, t.name) for t in cls.objects.all()]


class Key(DiscussionMixin, HistoricalMixin, Document):
    """ Named slot within a node that contains values.

    Equivalent to an SQL column.
    """

    name = StringField(max_length=1024, required=True)
    comment = StringField(max_length=4096)
    soft_type = ReferenceField(Type)
    size = IntegerField(max_length=128)
    position = IntegerField(max_length=128)
    primary = BooleanField()


class Node(DiscussionMixin, HistoricalMixin, Document):
    """ Equivalent to a table. Contains records for data.

    A Path may only have one Node, but several Paths pay lead to a Node. For
    example:

        /paint/warm/orange      --+
        /spectrum/lower/orange  --+--> Orange
    """

    title = StringField(max_length=2048)
    description = StringField(max_length=4096)
    keys = ListField(ReferenceField(Key), required=True)

    def do_select(self, key_names=None, filter_args=None, limit=100, offset=0,
                  expand_keys=False, expand_slots=False):
        """ Perform a select on a node, returning the resulting rows.

        :param key_names: Key names to select

        :param filter_args: Arguments to filter.

        :param limit: How many rows to return.

        :param offset: Starting row.

        :param expand_keys: If set to True, will expand the keys. See note
            below.

        :param expand_slots: If set to True, will expand the slots. See note
            below.

        Note
        ====

        expand_keys and expand_slots
        ============================

        Since keys and slots are objects, typically you would not want to get
        the entire object. We're mostly interested in the key name. Therefore,
        if `expand_keys` is set to True, only the key name will be used in
        a dict format. If `expand_keys` is set to false, a tuple will be
        returned instead of a dict. If `expand_values` is set to True, then only
        the value representation (as returned from the associated microservice)
        will be returned.

        Here are examples to drive home the point:

        ================    ==================      ===========================
        expand_keys         expand_slots            Returned Row
        ================    ==================      ===========================
        False               False                   {"key": "slot", ...}
        False               True                    {"key": {id: ...}, ...}
        True                False                   ({id: ...}, "slot")
        True                True                    ({id: ...}, {id: ...}, ...)
        ================    ==================      ===========================

        """
        keys = key_names or [k.name for k in self.keys]
        keys = [k for k in self.keys if k.name in keys]
        rows = []
        if filter_args is None:
            for rownum in range(offset, offset+limit):
                if expand_keys:
                    row = []
                else:
                    row = {}
                for key in self.keys:
                    slot = Slot.objects(key=self, row=rownum)
                    if slot.count() > 0:
                        logger.warn("More than 1 slot returned "
                                    "(key={}, row={})".format(key, row))
                    slot = slot.first()
                    if expand_keys:
                        row.append(key)
                        if expand_slots:
                            row.append(slot)
                    else:
                        if expand_slots:
                            row[key.name] = slot
                        else:
                            row[key.name] = slot.get_repr()
                rows.append(row)
            return rows

    @property
    def paths(self):
        """ Get paths associated with node. """
        return Path.objects(node__in=[self, ]).all()


class Path(DiscussionMixin, HistoricalMixin, Document):
    """ Heirarchical organization of Node.

    Think of this like folders or directories on a filesystem.

    """

    name = StringField(max_length=409, required=True)
    parent = ReferenceField('Path')
    node = ReferenceField(Node)

    @property
    def paths(self):
        """ Get a QuerySet representing this path's sub-paths. """
        return type(self).objects(parent=self)

    def string(self, sep='/'):
        if self.parent:
            return self.parent.string(sep) + sep + self.name
        return sep + self.name

    def make(self, user, path):
        """ Automagically create path children based on `path`. """
        (head, tail) = path_head_tail(path)
        p = self.paths.filter(name=head).first()
        if p is None:
            p = Path(name=head, parent=self)
            p.save(user)
        if tail is not None:
            p.make(user, tail)
        return p

    def _find(self, path):
        if path is None:
            return self
        (head, tail) = path_head_tail(path)
        p = self.paths.filter(name=head).first()
        if p is None:
            return None
        return p._find(tail)

    @classmethod
    def find(cls, path):
        (head, tail) = path_head_tail(path)
        p = cls.objects(name=head, parent=None).first()
        if p is None:
            return None
        return p._find(tail)

    @classmethod
    def create(cls, user, full_path):
        if cls.find(full_path) is not None:
            raise OneBaseException('E-206', path=full_path)
        (head, tail) = path_head_tail(full_path)
        p = cls.objects(name=head, parent=None).first()
        if p is None:
            p = Path(name=head)
            p.save(user)
        if tail is not None:
            p.make(user, tail)
        return p


def create_node_at_path(user, full_path, node):
    """ Convenience method to create a node at a given path.

    :param user: User creating the path

    :param full_path: Full path specification for node (e.g.
        '/path/to/node')

    :param node: Node to create at the path.

    :return: Path that was modified or created.
    """
    if not user.can_any('create_path'):
        raise OneBaseException('E-201', user=user,
                               permissions=['create_path', ])
    path = Path.find(full_path)
    if path and path.node is not None:
        raise OneBaseException('E-204', path=path)
    if not path:
        logger.debug("Creating new path {}".format(full_path))
        path = Path.create(user, full_path)
    path.node = node
    path.save(user)
    return node


class Slot(DynamicDocument, DiscussionMixin):
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
