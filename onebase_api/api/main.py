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

from http import HTTPStatus as STATUS
import logging

from onebase_api.onebase import ApiResponse
from onebase_common.exceptions import OneBaseException

from onebase_api.api.validators import validator_views
# from onebase_api.api.representers import repr_views
from onebase_api.api.representers import slot_views
from onebase_api import app

logger = logging.getLogger(__name__)

BLUEPRINTS = (
    validator_views,
    # repr_views,
    slot_views,
)


@app.route('/', methods=['GET', ])
def hello():
    return ApiResponse()


for bp in BLUEPRINTS:
    app.register_blueprint(bp)


app.response_class = ApiResponse


@app.errorhandler(OneBaseException)
def handle_onebase_exception(obe):
    """ Wrap an ApiResponse around the exception. """
    return ApiResponse(status=STATUS.INTERNAL_SERVER_ERROR,
                       data={
                        'exception': {
                            'error_code': obe.error_code,
                            'message': str(obe)
                        }
                       })
