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

from onebase_api import app
from onebase_api.onebase import ApiResponse
from onebase_common import settings

logger = logging.getLogger(__name__)

def prepend_url(url):
    """ Prepend a URL predicate to a URL. """
    return '/api/' + settings.API_VERSION + '/doc' + url

_ = prepend_url

@app.route(_('/'), methods=['GET',])
def all_doc():
    return ApiResponse(data=app.rest_docs)
