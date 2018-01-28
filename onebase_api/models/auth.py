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
from secrets import token_urlsafe

from mongoengine import (
    Document,
    StringField,
    ListField,
    EmailField,
    ReferenceField,
    DateTimeField,
    BooleanField,
    DynamicDocument,
)

from onebase_common.settings import ADMIN_GROUPS
from onebase_api.models.mixin import (
    JsonMixin
)
from onebase_api.fields import (
    ForgivingURLField
)
from itertools import (
    chain,
)

logger = logging.getLogger()


SEX_CHOICES = (
    ('m', 'Male'),
    ('m', 'Female'),
)


class Group(JsonMixin, Document):
    """ Collection of users with certain permissions. """

    name = StringField(primary_key=True)
    permissions = ListField(StringField(max_length=1024))

    @property
    def users(self):
        return User.objects(groups__in=[self, ]) or []

    def __str__(self):
        return super(Group, self).__str__()


class User(JsonMixin, DynamicDocument):
    """ An account on 1base. """

    email = EmailField(max_length=1024, required=True, unique=True)
    password = StringField(max_length=1027, required=True)
    username = StringField(max_length=120, required=False, unique=True,
                           sparse=True)
    groups = ListField(ReferenceField(Group), default=list())

    # attributes required by flask-login
    # https://flask-login.readthedocs.io/en/latest/
    # `is_authenticated` and `is_anonymous` are attibutes in constructor
    is_active = BooleanField(default=False)
    verification = StringField(default=token_urlsafe())

    # Personal "business" information
    sex = StringField(choices=SEX_CHOICES)
    first_name = StringField(max_length=1024)
    middle_name = StringField(max_length=1024)
    last_name = StringField(max_length=1024)
    birth_date = DateTimeField()
    phone_number = StringField(max_length=48)

    # Developer information
    api_key = StringField()

    # Frilly information
    avatar = ForgivingURLField()

    def __init__(self, *args, **kwargs):
        """ Construct a new user. """
        self.is_authenticated = False
        self.is_anonymous = False
        super(User, self).__init__(*args, **kwargs)

    def get_id(self):
        """ Get ID of the user.

        Required by
        `flask-login <https://flask-login.readthedocs.io/en/latest/>`_
        """
        return self.id.encode('unicode')

    def generate_api_key(self):
        self.api_key = token_urlsafe()

    @property
    def all_permissions(self):
        """ Return all permissions used by the user. """
        perms = []
        for g in self.groups:
            perms.extend(g.permissions)
        return list(tuple(perms))

    @property
    def is_admin(self):
        """ Return True if user is in any ADMIN_GROUPS group. """
        return len([g for g in self.groups if g.name in ADMIN_GROUPS]) > 0

    def can_any(self, *permissions):
        """ Return True if user can use any of the permissions.

        NOTE: By default will return True if group name is listed in
        onebase_common.settings.ADMIN_GROUPS

        """
        if self.is_admin:
            return True
        ap = self.all_permissions
        for p in permissions:
            if p in ap:
                return True
        return False

    def can_all(self, *permissions):
        """ Return True if user can use *all* permissions listed.

        NOTE: By default will return True if group name is listed in
        onebase_common.settings.ADMIN_GROUPS

        :param permissions: Permissions for the user.

        """
        if self.is_admin:
            return True
        ap = self.all_permissions
        for p in permissions:
            if p not in ap:
                return False
        return True

    def to_json(self):
        return super(User, self).to_json(omit=['password'])
