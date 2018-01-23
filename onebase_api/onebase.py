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

from json import dumps
from http import HTTPStatus as STATUS
from flask import (
    Flask,
    Response,
    # make_response,
    jsonify,
)

from onebase_api.exceptions import OneBaseException
from onebase_common import settings


class ApiResponse(Response):
    """ Custom response object returned by the API.

    Response is formatted as a JSON REST response.

    """

    def __init__(self, response=None, status=STATUS.OK, headers=None,
                 mimetype='application/json',
                 content_type='application/json',
                 direct_passthrough=False,
                 request=None,
                 data={},
                 message=None):
        """ Construct a new ApiResponse.

        :param request: Original request

        :param data: JSON-formatted data

        :param status: HTTP status.

        :param headers: HTTP headers

        :param mimetype: Mimetype

        :param content_type: Content type

        :param direct_passthrough: Direct direct_passthrough

        :param message: Optional message.

        """
        if isinstance(status, STATUS):
            status = status.value
        status = str(status)
        body = dict(
            info=settings.RESPONSE_INFO,
            status=status,
            data=data,
            message=message,
        )
        return super(ApiResponse, self).__init__(response=dumps(body),
                                                 status=status,
                                                 headers=headers,
                                                 mimetype=mimetype,
                                                 content_type=content_type)

class OneBaseApp(Flask):

    def __init__(self, *args, **kwargs):
        self.rest_docs = {}
        super(OneBaseApp, self).__init__(*args, **kwargs)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """ Add the url rule, but also add documentation.
        """
        if view_func:
            self.rest_docs[rule] = {
                'documentation': view_func.__doc__,
                'options': options,
            }
        else:
            logger.warn('no view func specified')
        return super(OneBaseApp, self).add_url_rule(rule, endpoint, view_func,
                                                    **options)


_app = OneBaseApp(__name__)


@_app.errorhandler(OneBaseException)
def handle_onebase_exception(obe):
    """ Wrap an ApiResponse around the exception. """
    return ApiResponse(status=STATUS.INTERNAL_SERVER_ERROR,
                       data={
                        'exception': {
                            'error_code': obe.error_code,
                            'message': str(obe)
                        }
                       })


_app.response_class = ApiResponse
app = _app
