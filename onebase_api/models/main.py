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
    LazyReferenceField,
    GenericLazyReferenceField,
    CASCADE,
    EmbeddedDocument,
    EmbeddedDocumentListField,
)
import requests

from onebase_api.models.discussion import (
    Discussion
)
from onebase_api.models.mixin import (
    JsonMixin,
    HistoricalMixin,
    DiscussionMixin,
)
from onebase_common.util import (
    path_split,
    path_head_tail,
    idict,
)

logger = logging.getLogger(__name__)


class Type(JsonMixin, Document):
    """ Basic type for databases. """

    name = StringField(max_length=120, unique=True)
    repr = ForgivingURLField()
    is_primitive = BooleanField(default=False)
    validator = ForgivingURLField()

    def validate_value(self, value, size, content_type='application/json',
                       clean=False):
        """ Validate the value based on the type.

        :param value: Value to validate.

        :param size: Size of the value (given by the Key)

        :parm clean: Passed in from parent validate() method.

        :return: True on success, raise OneBaseException if invalid.

        """
        headers = {}
        data = {
            'value': value,
            'size': size,
        }
        logger.debug('validating {} with {}'
                     .format(data, self.validator))
        response = requests.post(self.validator, json=data, headers=headers)
        if response.status_code == 200:
            return True
        raise OneBaseException('E-101', message=response.content)

    def represent_value(self, value, headers={}, environment={}):
        """ Represent a value.

        :param value: Value to represent

        :param headers: Headers to pass to the request

        :param repr_kwargs: Keyword arguments to the representer

        :return: Response body.

        """
        headers = headers or {}
        data = {'value': value, 'environment': environment}
        logger.debug('representing {} with {}'.format(data, self.repr))
        response = requests.post(self.repr, json=data, headers=headers)
        if response.status_code == 200:
            return response.text
        raise OneBaseException('E-101', message=response.content)


    @classmethod
    def as_select(cls):
        """ Convenience method for getting a select-style list. """
        return [(t.id, t.name) for t in cls.objects.all()]


class Key(DiscussionMixin, HistoricalMixin, JsonMixin):
    """ Named slot within a node that contains values.

    Equivalent to an SQL column.
    """

    name = StringField(max_length=1024, required=True)
    comment = StringField(max_length=4096)
    soft_type = LazyReferenceField('Type', required=True,
                                   passthrough=True)
    size = IntegerField(max_length=128, required=True)
    position = IntegerField(max_length=128)
    primary = BooleanField()

    @property
    def node(self):
        return Node.objects(keys__in=[self.id, ]).first()


class Node(DiscussionMixin, HistoricalMixin, Document):
    """ Equivalent to a table. Contains records for data.

    A Path may only have one Node, but several Paths pay lead to a Node. For
    example:

        /paint/warm/orange      --+
        /spectrum/lower/orange  --+--> Orange
    """

    title = StringField(max_length=2048)
    description = StringField(max_length=4096)
    keys = ListField(LazyReferenceField(Key, passthrough=False),
                     required=True)

    def get_keys(self):
        return Key.objects(id__in=self.keys).all()

    @property
    def row_count(self):
        """ Count the number of rows in the Node.

        TODO: This can be very bad for very large row counts since
        all Slots are loaded if slots.count() > 0 (in order to get
        the slot row)

        """
        slots = Slot.objects(key__in=self.keys).fields(row=1)
        # logger.debug('slots: {}'.format(slots.all()))
        if slots.count() == 0:
            return 0
        return max([s.row for s in slots.all()])+1


    def do_select(self, key_names=None, filter_args=None, limit=100, offset=0,
                  expand_keys=False, expand_slots=False, environment={}):
        """ Perform a select on a node, returning the resulting rows.

        :param key_names: Key names to select

        :param filter_args: Arguments to filter.

        :param limit: How many rows to return.

        :param offset: Starting row.

        :param expand_keys: If set to True, will expand the keys. See note
            below.

        :param expand_slots: If set to True, will expand the slots. See note
            below.

        :param environment: Environment to pass to the representer.

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
        self.select_related()
        # keys = [k for k in self.keys if k.fetch().name in keys]
        rows = idict()
        if filter_args is None:
            logger.debug('Selecting rows {} - {}'.format(offset, offset+limit))
            for rownum in range(offset, min(offset+limit, self.row_count)):
                logger.debug(' - row # {}'.format(rownum))
                row = idict()
                col_num = 0
                for key_ref in self.get_keys():
                    key = key_ref
                    col_num += 1
                    logger.debug("Selecting for key={}, rownum={}, col_num={}"
                                 .format(key.id, rownum, col_num))
                    slot = Slot.objects(key=key.id, row=rownum)
                    logger.debug('{} slots'.format(slot.count()))
                    if slot.count() == 0:
                        continue
                    if slot.count() > 1:
                        logger.warn("More than 1 slot returned "
                                    "(key={}, row={})".format(key, row))
                    slot = slot.first()
                    if not expand_keys and not expand_slots:
                        row[key.name] = slot.value
                    if expand_keys and not expand_slots:
                        row[col_num] = [key, slot.value]
                    if not expand_keys and expand_slots:
                        row[key.name] = slot.get_repr(environment=environment)
                    if expand_keys and expand_slots:
                        row[col_num] = [key,
                                        slot.get_repr(environment=environment)]
                rows[rownum] = row
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

    @property
    def string2(self):
        return self.string()

    def make(self, user, path):
        """ Automagically create path children based on `path`. """
        (head, tail) = path_head_tail(path)
        p = self.paths.filter(name=head).first()
        if p is None:
            p = Path(name=head, parent=self)
            p.save(user)
        if tail is not None:
            return p.make(user, tail)
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
            return p.make(user, tail)
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
        raise OneBaseException('E-204', path=path.string2)
    if not path:
        logger.debug("Creating new path {}".format(full_path))
        path = Path.create(user, full_path)
    path.node = node
    path.save(user)
    return path


class Slot(DynamicDocument, DiscussionMixin, JsonMixin):
    """ Data value.

    Equivalent to a single cell in an SQL table.

    But what's unique about 1Base's values is that it's not constrained to
    basic types (here's looking at you, BLOB).

    Besides the normal primitives (INT, BOOL, etc.), a type can be anything,
    including multimedia, or even a reference to antoher table. Typically
    the value is represented by the `type.repr` URL.
    """

    key = LazyReferenceField('Key', required=True, passthrough=True)
    row = IntegerField(max_length=128, unique_with='key', required=True)
    value = DynamicField(required=True)

    def __init__(self, *args, **kwargs):
        if kwargs.get('_created', False):
            logger.debug("args={}, kwargs={}".format(args, kwargs))
            kwargs['row'] = kwargs.get('row', kwargs['key'].node.row_count)
        super(Slot, self).__init__(*args, **kwargs)

    def validate(self, clean=True):
        """ Validate this value.

        Validation is a bit unique for 1Base. We're calling a microservice
        (again) to verify the value is valid.
        """
        # Grab the validator
        st = self.key.soft_type.fetch()
        logger.debug(st)
        st.validate_value(self.value, self.key.size, clean=clean)

    def get_repr(self, headers={}, environment={}):
        st = self.key.soft_type.fetch()
        logger.debug(st)
        return st.represent_value(self.value,
                                  headers=headers,
                                  environment=environment)
