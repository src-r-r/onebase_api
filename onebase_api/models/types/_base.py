

import logging
import re

from flask import (
    Response
)

from onebase_common.exceptions import OneBaseException
from onebase_common.util import mimetype_to_method

logger = logging.getLogger(__name__)

class TypeBase(object):

    names = None
    maximum_size = 1024

    def validate(self, value):
        """ Validate a value

        :param value: Value to validate.
        """
        if len(value) > self.maximum_size:
            raise OneBaseException('E-100',
                                   expected=self.maximum_size,
                                   given=len(value))
        return True

    def prepare(self, slot):
        """ Prepare the slot for storage.

        :param slot: Slot to store.

        :return: MongoDB-friendly value for storage.
        """
        raise NotImplementedError()

    def render(self, slot, requested_mimetype='application/html', **kwargs):
        """ Controls how the slot is rendered.

        :param slot: slot to render

        :param kwargs: Keyword arguments specific to the type
        """
        typename = type(self).__name__
        mname = 'render_' + mimetype_to_method(requested_mimetype)
        dflt_mname = 'render_default'
        if hasattr(self, mname):
            return getattr(self, mname)(slot, **kwargs)
        logger.debug('{}.{} not found. Using {}.{}'
                     .format(typename, mname, typename, dflt_mname))
        getattr(self, mname)(slot, **kwargs)

    def respond(self, slot, requested_mimetype='application/html', **kwargs):
        return Response(self.render(slto, requested_mimetype, **kwargs))


class RegexValidationMixin(TypeBase):

    EXPRESSION = None

    def validate(self, value):
        return (super(RegexValidationMixin, self).validate(value)
                and re.compile(EXPRESSION).match(value) is not None)
