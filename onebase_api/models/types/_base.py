

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
        if len(str(value)) > self.maximum_size:
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

    def _call_function(self, prefix, requested_mimetype, slot,
                       dflt_postfix='default',
                       **kwargs):
        typename = type(self).__name__
        mname = prefix + mimetype_to_method(requested_mimetype)
        dflt_mname = prefix + dflt_postfix
        if hasattr(self, mname):
            return getattr(self, mname)(slot, **kwargs)
        logger.debug('{}.{} not found. Using {}.{}'
                     .format(typename, mname, typename, dflt_mname))
        return getattr(self, dflt_mname)(slot, requested_mimetype, **kwargs)

    def get_attrs(self, slot, requested_mimetype, **kwargs):
        """ Get attributes for the slot.

        :param requested_mimetype: Mimetype.

        :param slot: The slot to be rendered, in case it's relevant.

        :param kwargs: Additional arguments.

        :return: dict of attributes, e.g. for HTML tag.
        """
        return self._call_function('get_attrs_', requested_mimetype, slot,
                                   **kwargs)

    def render(self, slot, requested_mimetype='application/html', **kwargs):
        """ Controls how the slot is rendered.

        :param slot: slot to render

        :param kwargs: Keyword arguments specific to the type
        """
        return self._call_function('render_', requested_mimetype, slot, **kwargs)

    def respond(self, slot, requested_mimetype='application/html', **kwargs):
        return Response(self.render(slot, requested_mimetype, **kwargs))


class RegexValidationMixin(TypeBase):

    EXPRESSION = None

    def validate(self, value):
        return (super(RegexValidationMixin, self).validate(value)
                and re.compile(self.EXPRESSION).match(str(value)) is not None)
