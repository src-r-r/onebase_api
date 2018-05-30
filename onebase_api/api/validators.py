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

import re
import logging

from http import HTTPStatus as STATUS
from flask import (
    Blueprint,
    request,
    # make_response
)

from mongoengine import connect

from onebase_common import settings
from onebase_common.log.setup import configure_logging
from onebase_common.exceptions import OneBaseException
from onebase_api.onebase import (
    ApiResponse,
    OnebaseBlueprint,
    )
from onebase_api import app

configure_logging()

""" Regular expressions used for validation.
"""
RE_INT = re.compile(r'^\-?\d+$').match
RE_BOOLEAN = re.compile(r'^(false|true|1|0)$', re.I).match
RE_FLOAT = re.compile(r'^\-?\d+\.\d+$').match

# Represents a "forgiving" URI.
# https://regex101.com/r/wjsGig/4
# Probably needs to be worked on. Hence the URL :-)
RE_URI = re.compile(r'^(\w{1,5}\:\/\/)?' # Protocol (e.g. https://)
                    r'(([\w\d\-](\.[\w\d\-])*)+)?' # Domain (e.g. example.com)
                    r'(\/([^\?]\/?)*)?' # Path (e.g. /path/to/example/)
                    r'(\?([^\=]+\=[^\&]+)*)?$'
                    ).match

logger = logging.getLogger(__name__)

validator_views = OnebaseBlueprint('validators', __name__,
                                   url_prefix='/validate')

@app.errorhandler(OneBaseException)
def handle_obe(obe):
    return Response(obe.to_json(), status=STATUS.INTERNAL_SERVER_ERROR)

def make_validation_response(is_valid, ok_status=STATUS.OK,
                             error_status=STATUS.INTERNAL_SERVER_ERROR):
    """ Make an API response from a validation result.

    :param is_valid: True if the validation was succcessful.

    :param ok_status: HTTP status to use if a validation passes.

    :param error_status: HTTP status to use if a validation fails.

    :return: ApiResponse object
    """
    if is_valid:
        return ApiResponse(status=ok_status)
    else:
        return ApiResponse(status=error_status)

def get_parts():
    body = request.get_json()
    for req in ('value', 'size'):
        if not body.get(req, None):
            raise OneBaseException('E-102', keys=[req, ])
    return (str(body['value']), int(body['size']))

def basic_regex_validation(REGEX_FUNC):
    """ Validate a slot by a given regex `match` function.

    This method will also check the length of the value. If the length of the
    `Type` is greater than the length of the slot, return False.

    :param REGEX_FUNC: Regular expression `match` function (or similar)

    :return: True if request's value is valid, False otherwise.
    """
    (value, length) = get_parts()
    if len(value) > length:
        raise OneBaseException('E-100',
                               key='value',
                               expected=length,
                               given=len(value))
    if not REGEX_FUNC(value):
        raise OneBaseException('E-101', message="Invalid format")
    return (length is not None) and (len(value) < length and REGEX_FUNC(value))


@validator_views.route('/', methods=['GET', ])
def validate():
    """ Get a list of the validators. """
    data = {
        'validators': {},
    }
    for (path, f) in validator_views._routes.items():
        data['validators'].update(
            {
                path: {
                    'name': f.__name__,
                    'doc': f.__doc__.split('\n'),
                }
            }
        )
    return ApiResponse(data=data)


@validator_views.route('/int', methods=['POST', ])
def validate_int():
    """ Validate an integer.

    .. request::
        body:
            value:
                type: str
                description: physical value of the slot
            size:
                type: int
                description: maximum size allowed for the value.

    .. response:
        status: 200 if validation passes, another error code otherwise.
    """
    return make_validation_response(basic_regex_validation(RE_INT))


@validator_views.route('/string', methods=['POST', ])
def validate_str():
    """ validate a string.

    .. request::
        body:
            value:
                type: str
                description: physical value of the slot
            size:
                type: int
                description: maximum size allowed for the value.

    .. response:
        status: 200 if validation passes, another error code otherwise.

    """
    (value, length) = get_parts()
    return make_validation_response(len(value) < length)


@validator_views.route('/boolean', methods=['POST', ])
def validate_boolean():
    """ Validate a boolean value.

    .. request::
        body:
            value:
                type: str
                description: physical value of the slot
            size:
                type: int
                description: maximum size allowed for the value.

    .. response:
        status: 200 if validation passes, another error code otherwise.

    """
    return make_validation_response(basic_regex_validation(RE_BOOLEAN))


@validator_views.route('/float', methods=['POST', ])
def validate_float():
    """ Validate a float value.

    .. request::
        body:
            value:
                type: str
                description: physical value of the slot
            size:
                type: int
                description: maximum size allowed for the value.

    .. response:
        status: 200 if validation passes, another error code otherwise.
    """
    return make_validation_response(basic_regex_validation(RE_FLOAT))


@validator_views.route('/image', methods=['POST', ])
def validate_image():
    """ Validate an image.

    .. request::
        body:
            value:
                type: str
                description: URL to an image (A path will assume relative.)
            size:
                type: int
                description: maximum size allowed for the value.

    .. response:
        status: 200 if validation passes, another error code otherwise.
    """
    return make_validation_response(basic_regex_validation(RE_URI))
