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

from onebase_api.models.types import TypeBase

class StringType(TypeBase):

    NAMES = [
        'STRING',
    ]

    def get_attrs_application_html(self, slot, **kwargs):
        return dict(type='text/plain')

    def get_attrs_default(self, requested_mimetype, slot, **kwargs):
        return {}

    def prepare(self, slot):
        return str(slot.value)

    def render_default(self, slot, **kwargs):
        return str(slot.value)
