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
from json import dumps

from os.path import join
import uuid
from urllib import (
    parse,
)

from onebase_api.fields import (
    ForgivingURLField,
    SlugField,
    )
from onebase_common.exceptions import OneBaseException
from onebase_common.render import (
    HtmlRenderer,
)
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
    UUIDField,
)
import requests

from onebase_api.models.discussion import (
    Discussion
)
from onebase_common.models.mixin import (
    JsonMixin,
    HistoricalMixin,
    DiscussionMixin,
)
from onebase_api.models.types import TYPE_SELECTION
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
    soft_type = StringField(required=True, max_length=2049,
                        choices=TYPE_SELECTION.keys())
    size = IntegerField(max_length=128, required=True)
    position = IntegerField(max_length=128)
    is_primary = BooleanField(default=False)

    @property
    def type(self):
        """ Get the class type associated with this key. """
        return TYPE_SELECTION[self.soft_type]

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
    rows = ListField(UUIDField())

    def syncronize_rows(self):
        """ Syncronize the row IDs. """
        slots = Slot.objects(key__in=self.get_keys).all()
        self.rows = []
        for s in slots:
            if s.row_id not in self.rows:
                self.rows.append(s.row_id)

    def drop_rows(self, *row_ids):
        """ Drop rows with the given row_id. """
        Slot.objects(key__in=self.keys, row_id__in=row_ids).delete()
        slot.syncronize_rows()

    def get_keys(self):
        """ Get keys of the node. """
        return Key.objects(id__in=self.keys).all()

    def get_row_id(self, row_num=None):
        """" Get a row ID from a row number.

        :param row_num: Optional. Row number from which to get row ID.
            Ommitting will return the last row ID.

        :return: Row ID of specified row_num, or 0 if no rows are found.

        """
        rc = self.row_count
        if rc is 0:
            return 0
        row_num = row_num or rc-1
        slot = Slot.objects(key__in=self.keys, row_num=row_num).first()
        if not slot:
            return 0
        return slot.row_num

    def insert(self, user, *slot_params, **kwargs):
        """ Insert a new row with a list of slot definitions.

        :param slot_params: A list of dicts. Example:

            insert([ # start of 1st new row
                    { 'key': key1, 'value': 4, },
                    { 'key': key2, 'value': 10, },
                    ...
                ],
                [ # start of 2nd new row
                    { 'key': key1, 'value': 13, },
                    { 'key': key2, 'value': 33, },
                    ...
                ])
            ]

        :param row_id: Row ID of the row to insert AFTER

        :parm row: Row number of the row to insert AFTER. Will take precedence
            over `row_id`.

        :param error_action: Action taken if an error occurs. Options:

        :`give_up`:
            Simply give up and throw an exception.
        :`rollback`:
            DEFAULT. Will do it's best to roll back the changes. Throws the
            error anyway.
        :`swallow`:
            Ignore the error and continue as if nothing happened.

        :return: Number of rows inserted.

        """
        row_id = kwargs.get('row_id', None)
        if not row_id:
            row_num = kwargs.get('row', self.row_count)
            row_id = self.get_row_id(row_num)

        error_action = kwargs.get('error_action', 'rollback').lower()
        if error_action not in ('give_up', 'rollback', 'swallow'):
            raise AttributeError("Invalid `error_action`")

        n_rows = 0
        _rollback = []

        for slot_row in slot_params:
            for slot_args in slot_row:
                try:
                    # Generate a unique uuid for this row.
                    insert_row_id = uuid.uuid4.hex()
                    self.rows.append(insert_row_id)
                    slot_args['row_id'] = insert_row_id
                    slot = Slot(*slot_args)
                    _rollback.append(slot)
                    slot.save(user, do_row_sync=False)
                except Exception as e:
                    if error_action == 'give_up':
                        raise e
                    if error_action == 'rollback':
                        for r in _rollback:
                            logger.warn('ROLL BACK {}...'.format(r))
                            Slot.objects(id=r.id).delete()
                        raise e
                    if error_action == 'swallow':
                        logger.error(e)
                        logger.error('swallow action, so continuing...')
                finally:
                    n_rows += 1
        return n_rows

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

    def do_select(self, client_id,
                  key_names=None, filter_args=None, limit=100, offset=0,
                  expand_keys=False, expand_slots=False,
                  mimetype='application/html', render_kwargs={}):
        """ Perform a select on a node, returning the resulting rows.

        :param client_id: Primary Key ID of the Client requesting the data.

        :param key_names: Key names to select

        :param filter_args: Arguments to filter.

        :param limit: How many rows to return.

        :param offset: Starting row.

        :param expand_keys: If set to True, will expand the keys. See note
            below.

        :param expand_slots: If set to True, will expand the slots. See note
            below.

        :param environment: Environment to pass to the representer.

        :param renderer: Render to use. NOTE: I don't like the use of renderers.
            I need to find a solution that's as environment-agnostic as I can
            get. For the prototypes, however, they'll stay.

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
                    # renderer = RendererClass()
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
                    if expand_slots:
                        """ IMPORTANT SECTION """
                        val = {'value': slot.id,
                               'attrs': slot.get_attrs(mimetype,
                                                       **render_kwargs)}
                        """ END IMPORTANT SECTION """
                        if expand_keys:
                            row[col_num] = [key, val]
                        else:
                            row[key.name] = val
                rows[rownum] = row
            return rows

    @property
    def paths(self):
        """ Get paths associated with node. """
        return Path.objects(node__in=[self, ]).all()

    def save(self, *args, **kwargs):
        """ Save the current Node.

        :param do_row_sync: Whether to perform row syncronization. default=True

        :see: HistoricalMixin.save

        """
        super(Node, self).save(*args, **kwargs)
        if kwargs.get('do_row_sync', False):
            self.syncronize_rows()
        super(Node, self).save(*args, **kwargs)


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
        """ Get the path's full path string. """
        if self.parent:
            return self.parent.string(sep) + sep + self.name
        return sep + self.name

    @property
    def string2(self):
        """ Get the path's full path string. (assumes sep='/') """
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
        """ Recursively find a path at `path`.

        :param path: Full path, e.g. ('/path/to/node')

        :return: The path found, or `None` if no path was found.
        """
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
    row_num = IntegerField(max_length=128, unique_with='key', required=True)
    row_id = UUIDField(binary=False, required=True)
    value = DynamicField(required=True)

    def __init__(self, *args, **kwargs):
        if kwargs.get('_created', False):
            logger.debug("args={}, kwargs={}".format(args, kwargs))
            kwargs['row'] = kwargs.get('row', kwargs['key'].node.row_count)
        super(Slot, self).__init__(*args, **kwargs)

    def save(self, user):
        """ Rearrange the row_num and row_id before saving. """
        self.row_num = self.row_num or 0
        while (Slot.objects.filter(key=self.key, row_num=self.row_num)):
            logger.debug("Incrementing self.row_num")
            self.row_num = self.row_num + 1
        return super(Slot, self).save(user)

    @property
    def is_reference(self):
        return str(self.value).startswith('onebase://')

    @property
    def type(self):
        logger.debug("slot.type - fetching key {}".format(self.key))
        return self.key.fetch().type

    @property
    def is_valid_reference(self):
        """ Return True if the value is a valid reference.

        Note this will return False if the path is invaild as well.

        """
        try:
            return self.get_reference is not None
        except Exception as e:
            return False

    @property
    def get_reference(self):
        """ Get the slot's reference.

        If a slot contains a reference to another slot, get it.

        A reference is in the format:

            onebase://<slot_id>
        """
        parts = None
        if str(self.value).startswith('onebase://'):
            parts = urlparse(self.value)
        else:
            return None
        slot_id = parts.net_loc
        if Slot.objects.find(id=slot_id).first() is None:
            raise OneBaseException('E-103', url=self.value)

    def validate(self, clean=True):
        """ Validate this value.

        Validation is a bit unique for 1Base. We're calling a microservice
        (again) to verify the value is valid.
        """
        inst = self.type()
        return inst.validate(self.value)

    def prepare(self):
        inst = self.type()
        return inst.prepare(self)

    def render(self, requested_mimetype='application/html', **kwargs):
        inst = self.type()
        return inst.render(self, requested_mimetype, **kwargs)

    def respond(self, requested_mimetype='application/html', **kwargs):
        inst = self.type()
        return inst.respond(self, requested_mimetype, **kwargs)

    def get_attrs(self, requested_mimetype='application/html', **kwargs):
        inst = self.type()
        kwargs['requested_mimetype'] = requested_mimetype
        return inst.get_attrs(self, **kwargs)
