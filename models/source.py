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
    URLField,
    StringField,
)

from odi_api.models.mixin import (
    DiscussionMixin
)

COLLECTION_METHOD = (
    ('man', 'Manually Entered'),
    ('in', 'Internally Generated'),
    ('ex', 'Externally Generated'),
    ('ref', 'Referenced'),
)
DEFAULT_COLLECTION_METHOD = 'man'


class Source(DiscussionMixin, Document):
    """ Base class for a source. """

    collection_method = StringField(choices=COLLECTION_METHOD,
                                    required=True,
                                    default=DEFAULT_COLLECTION_METHOD
                                    )
    description = StringField()

    meta = {'allow_inheritance': True, }


class WebSource(Source):
    """ Web-based source. """

    url = URLField()


class SourcedDocument(object):
    """ Object that includes a source. """

    source = ReferenceField(Source, required=True)
