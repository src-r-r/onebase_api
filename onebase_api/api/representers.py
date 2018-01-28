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

from flask import (
    request,
    make_response,
    Response,
)

from onebase_common import settings
from onebase_common.log.setup import configure_logging
from onebase_api.exceptions import OneBaseException
from onebase_api.onebase import (
    ApiResponse,
    OnebaseBlueprint,
    )
from onebase_api import app

repr_views = OnebaseBlueprint('representers', __name__,
                              url_prefix='/repr')


def primitive_repr():
    """ Represent a primitive type. """
    body = request.get_json()

    environment = body.get('environment', {})
    try:
        return_format = environment['return_mimetype']
    except:
        return_format = 'application/json'

    if return_format == 'application/json':
        return ApiResponse(data={'repr': str(body.get('value')), })
    elif return_format == 'application/html':
        return Response(str(body.get('value')), mimetype=return_format)
    elif return_format == 'text/plain':
        return Response(str(body.get('value')), mimetype=return_format)


def media_repr(media_type):
    body = request.get_json()
    environment = body.get('environment', {})
    try:
        return_format = environment['return_mimetype']
    except:
        return_format = 'application/json'
    content_type = return_format
    try:
        static_url = environment['static_url']
    except:
        static_url = ''
    try:
        max_height = environment['scale']
    except:
        height_pct = '20px'
    if content_type == 'application/html':
        tag = '<{} src="{}{}" height="{}"/>'.format(media_type,
                                          static_url,
                                          str(body.get('value')),
                                          height_pct
                                          )
        return Response(tag, mimetype=return_format)
    elif content_type == 'application/json':
        return ApiResponse(data={
            'image': static_url + str(body.get('value')),
            })
    if content_type == 'image/png':
        # todo
        return ApiResponse()


@repr_views.route('/int', methods=['POST', ])
def repr_int():
    """ Represent an integer value.

    :param value: Value to represent

    :param args: Additional arguments used for validation
    """
    return primitive_repr()


@repr_views.route('/str', methods=['POST', ])
def repr_str():
    """ Represent a string value.

    :param value: Value to represent

    :param args: Additional arguments used for validation
    """
    return primitive_repr()


@repr_views.route('/image', methods=['POST', ])
def repr_internal_image():
    """ Represent an image.

    :param value: Image identification.

    :param args: Additional arguments used for validation

    TODO: return a raw stream with mimetype:
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types
    """
    return media_repr('img')


@repr_views.route('/', methods=['GET', ])
def represent():
    """ Get a list of the representers. """
    data = {
        'representers': {},
    }
    for (path, f) in repr_views._routes.items():
        if f.__name__ == 'represent':
            continue
        data['representers'].update(
            {
                path: {
                    'name': f.__name__,
                    'doc': f.__doc__.split('\n'),
                }
            }
        )
    return ApiResponse(data=data)
