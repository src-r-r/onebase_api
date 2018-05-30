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
from onebase_common.exceptions import OneBaseException
from onebase_api.models.main import (
    Slot,
)
from onebase_api.onebase import (
    ApiResponse,
    OnebaseBlueprint,
    )
from onebase_api import app

slot_views = OnebaseBlueprint('representers', __name__,
                              url_prefix='/slot')


@slot_views.route('/attrs/<slot_id>', methods=['GET', ])
def get_attrs(slot_id):
    slot = Slot.objects(id=slot_id).first()
    return ApiResponse(data=slot.get_attrs(**request.args))

@slot_views.route('/render/<slot_id>', methods=['GET', ])
def render_slot(slot_id):
    slot = Slot.objects(id=slot_id).first()
    return slot.respond(**request.args)
