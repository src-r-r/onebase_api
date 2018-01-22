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
    request,
    # make_response
)

from onebase_common import settings
from onebase_api.onebase import ApiResponse
from onebase_api.onebase import app

""" Regular expressions used for validation.
"""
RE_INT = re.compile(r'^[\d]+$').match

logger = logging.getLogger(__name__)


def prepend_url(url):
    """ Prepend a URL predicate to a URL. """
    return '/api/' + settings.API_VERSION + '/validate' + url


_ = prepend_url


def make_validation_response(is_valid, ok_status=STATUS.OK,
                             error_status=STATUS.NOT_ACCEPTABLE):
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


@app.route(_(''), methods=['POST', ])
def validate():
    """ Validate a value.

    .. request::
        body:
            value:
                type: str
                description: physical value of the slot
            length:
                type: int
                description: maximum size allowed for the value.

    .. response:
        status: 200 if validation passes, another error code otherwise.

    """
    return ApiResponse()


@app.route(_('/int'), methods=['POST', ])
def validate_int():
    """ Validate an integer. """
    body = request.get_json()
    val = body['value']
    return make_validation_response(RE_INT(val))