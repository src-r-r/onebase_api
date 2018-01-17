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
from mongoengine.fields import BaseField
import re

# https://regex101.com/r/wjsGig/3
RE_URI = re.compile(r'^(\w{1,5}\:\/\/)?' # Protocol (e.g. https://)
                    r'(([\w\d\-](\.[\w\d\-])*)+)?' # Domain (e.g. example.com)
                    r'(\/([\w\d\-]\/?)*)?' # Path (e.g. /path/to/example/)
                    r'(\?([^\=]+\=[^\&]+)*)?$'
                    ).match

RE_SLUG = re.compile(r'^[a-z\d\_\-]+$').match

class ForgivingURLField(BaseField):
    """ URL field that can handle relative URLS

    Essentially mongoengine's URLField but doesn't expect the URL to contain
    a protocol or even domain. Some valid URLs:

        - /path/to/file/
        - /path/to/file/?format=jpeg
        - example.com?param=1&other=2
    """

    def __init__(self, *args, **kwargs):
        super(ForgivingURLField, self).__init__(*args, **kwargs)

    def validate(self, value, clean=True):
        return RE_URI(value) is not None


class SlugField(BaseField):
    """ Machine-friendly string.

    Think of it like a variable name. Valid values:

        - `my-name`
        - `my_name`
        - `the_4th_one`
    """

    def validate(self, value, clean=True):
        return RE_SLUG(value) is not None
