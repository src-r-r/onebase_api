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
import os
import re
import importlib.util
import inspect
import itertools

logger = logging.getLogger(__name__)

# from onebase_common.util import in_list
from onebase_api.models.types._base import (TypeBase, RegexValidationMixin)

TypeBase = TypeBase
RegexValidationMixin = RegexValidationMixin

_SKIPPED_TYPES = [TypeBase, RegexValidationMixin]

__all__ = []

TYPE_SELECTION = {}

def recursive_find(item, l):
    if isinstance(l, (list, tuple)):
        return any([recursive_find(item, i) for i in l])
    # logger.debug('`{}` == `{}`? {}'.format(item, l, item.__name__ == l.__name__))
    return l.__name__ == item.__name__

HERE = os.path.dirname(__file__)
type_files = [os.path.join(HERE, f) for f in os.listdir(HERE)
              if f not in ('__init__.py', '_base.py')]
for tf in type_files:
    spec = importlib.util.spec_from_file_location(__name__, tf)
    if spec is None:
        logger.warn("Could not load spec from {}".format(tf))
        continue
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for (ClassName, Class) in vars(module).items():
        if not inspect.isclass(Class):
            continue
        if Class in _SKIPPED_TYPES:
            logger.debug("Skipping {} since it's abstract".format(ClassName))
            continue
        tree = inspect.getclasstree([Class])
        # logger.debug("Type tree: {}".format(tree))
        if not recursive_find(TypeBase, tree):
            logger.warn("I don't think {} is a type of TypeBase."
                        .format(ClassName))
            continue
        logger.debug("Adding {} to types".format(ClassName))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if not hasattr(Class, 'NAMES'):
            raise NotImplementedError('{}.NAMES'.format(ClassName))
        if not isinstance(Class.NAMES, (list, tuple, set)):
            raise TypeError("{}.NAMES must be an list-like type")
        TYPE_SELECTION[Class.NAMES[0].upper()] = Class

logger.debug("Loaded the following types:")
for TS in TYPE_SELECTION.items():
    logger.debug("{}: {}".format(*TS))
