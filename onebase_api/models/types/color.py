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

from onebase_api.models.types import (
    TypeBase,
    RegexValidationMixin,
    )

from PIL import Image
from onebase_common.exceptions import OneBaseException


class Color(RegexValidationMixin):

    NAMES = [
        'COLOR'
    ]

    SIZES = {
        'bit': 1,
        'micro': 25,
        'small': 75,
        'medium': 400,
        'large': 1024,
        'huge': 2048,
        }
    DEFAULT_SIZE='small'

    EXPRESSION = r'^\#[\w\d]{6,8}$'

    def prepare(self, slot):
        return slot

    def render_default(self, slot, size=DEFAULT_SIZE, include_alpha=True,
                       encode='PNG'):
        if size not in SIZES.keys:
            raise OneBaseException('E-503', value=size, key='size')
        size = (SIZES[size], SIZES[size]*1.5)
        value = slot.value
        pil_mode = 'RGBA'
        if not include_alpha:
            value = value[:7]
            pil_mode = 'RGB'
        image = Image.new(pil_mode, size, alpha)
        return image.tobytes(encode)
