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
import re
from json import (
    dumps
)

from mongoengine import (
    Document,
    ListField,
    ReferenceField,
    SortedListField,
    EmbeddedDocumentField,
    GenericEmbeddedDocumentField,
    DynamicDocument,
)

from mongoengine.fields import (
    BaseField,
)

from onebase_common.settings import DEFAULT_JSON_OMIT
from onebase_api.exceptions import OneBaseException

logger = logging.getLogger(__name__)

# https://regex101.com/r/nKLJ6r/1
RE_VALID = re.compile(r'^[a-z][\w\_]+$').match


class JsonMixin(object):
    """ Allows the object to be formatted as a JSON object. """

    meta = {
        'abstract': True
    }

    def to_json(self, level=1, omit=[]):
        data = {}
        omit = omit + DEFAULT_JSON_OMIT
        all_attrs = list(self.__class__.__dict__.keys())
        if level == 0:
            return type(self).__name__
        for b in self.__class__.__bases__:
            all_attrs.extend(list(b.__dict__.keys()))
        for a in all_attrs:
            if (a in omit) or (RE_VALID(a) is None):
                continue
            v = getattr(self, a)
            if callable(v):
                continue
            if isinstance(v, type(self)):
                logger.debug('{}.to_json'.format(a))
                data[a] = v.to_json(level-1)
                continue
            data[a] = str(v)
        return data

    def __str__(self):
        return str(self.to_json())

    def __repr__(self):
        return str(self.to_json())

    def __unicode__(self):
        return str(self.to_json())


class TimestampOrderableMixin(object):
    """ Class that contains a `timestamp` field.

    Overrides the comparison operators, so that the object can be sorted
    by date.
    """

    meta = {
        'abstract': True
    }

    def __gt__(self, other):
        return (isinstance(other, type(self))
                and self.timestamp > other.timestamp)

    def __lt__(self, other):
        return (isinstance(other, type(self))
                and self.timestamp < other.timestamp)


class DiscussionMixin(Document):
    """ Makes a document able to be discussed.

    Contains a refernce to discussions.

    """

    meta = {
        'abstract': True
    }

    discussions = ListField(ReferenceField('Discussion'))


class HistoricalMixin(DynamicDocument):
    """ Historical mixin class.

    Contains information on the Document being modified.

    """

    meta = {
        'abstract': True
    }

    history = SortedListField(GenericEmbeddedDocumentField('Action'),
                              ordering='timestamp')

    @property
    def creator(self):
        """ Get the user that created the Document. """
        if len(self.history) == 0:
            return None
        return self.history[0].user

    def save(self, user, *args, **kwargs):
        """ Save the document.

        Adds a "created" action to the history if this is an insert. Otherwise,
        adds a "modified" action.

        An exception will occur if the Document is read-only or if the user
        saving the Document does not have 'save_document' permissions.

        Obviously, we must modify the Document to change it's writablity.
        Therefore, a special `__modify_writability__` keyword argument will
        signal this case, and must be set to True. The user must also either
        be an admin or have the 'set_writability' permission.

        """
        logger.debug('save by user {}'.format(user))
        if self.is_readonly:
            if not (kwargs.get('__modify_writability__', False) and
                    user.can_any('set_writability')):
                raise OneBaseException('E-101', document=self)
        if not user.can_any('save_document'):
            logger.error('cannot save')
            raise OneBaseException('E-200', user=user)
        from onebase_api.models.history import Action
        event = Action.EVENT_MODIFY
        if len(self.history) == 0:
            event = Action.EVENT_CREATE
        action = Action(user=user, event=event)
        self.history.append(action)
        return super(HistoricalMixin, self).save(*args, **kwargs)

    @property
    def is_hidden(self):
        """ Return True if the Document is hidden. """
        if len(self.history) == 0:
            return False
        from onebase_api.models.history import Action
        for h in reversed(self.history):
            if h.event == Action.EVENT_HIDE:
                return True
            if h.event == Action.EVENT_SHOW:
                return False
        return False

    def set_readonly(self, user):
        """ Set the current document as READONLY. """
        if not user.can_any('set_writability'):
            raise OneBaseException('E-200', user=user)
        from onebase_api.models.history import Action
        self.history.append(Action(user=user, event=Action.EVENT_READONLY))
        self.save(user, __modify_writability__=True)

    def set_writable(self, user):
        """ Set the current document as WRITABLE. """
        if not user.can_any('set_writability'):
            raise OneBaseException('E-200', user=user)
        from onebase_api.models.history import Action
        self.history.append(Action(user=user, event=Action.EVENT_READONLY))
        self.save(user, __modify_writability__=True)

    @property
    def is_readonly(self):
        """ Return True if the document is read-only. """
        if len(self.history) == 0:
            return False
        from onebase_api.models.history import Action
        for h in reversed(self.history):
            if h.event == Action.EVENT_READONLY:
                return True
            if h.event == Action.EVENT_WRITABLE:
                return False
        return False

    @property
    def is_writable(self):
        """ Return True if the doucument is writable (not read-only). """
        return not self.is_readonly

    @property
    def is_shown(self):
        """ Return True if the Document is shown (not hidden). """
        return not self.is_hidden

    def hide(self, user):
        """ Hide the Document. """
        if not user.can_any('set_visibility'):
            raise OneBaseException('E-200', user=user)
        if self.is_hidden:
            return True
        from onebase_api.models.history import Action
        action = Action(user=user, event=Action.EVENT_MODIFY)
        self.history.append(action)
        self.save(user)

    def show(self, user):
        """ Show the Document. """
        if not user.can_any('set_visibility'):
            raise OneBaseException('E-200', user=user)
        if self.is_shown:
            return True
        from onebase_api.models.history import Action
        action = Action(user=user, event=Action.EVENT_MODIFY)
        self.history.append(action)
        self.save(user)
