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
import argparse
import os
import sys

from onebase_api.models import (
    # Type,
    Slot,
    Key,
    Node,
    Path,
)

pass

logger = logging.getLogger(__name__)

help = """ Simple CLI utility to upload all system icons to local instance of
1Base.

This is intended to be for testing only.
"""

parser = argparse.ArgumentParser(help=help)

parser.add_argument('icon_directory')
parser.add_argument('static_root_directory')

def create_node():
    types = [

    ]
    keys = [
        Key('')
    ]
    # node = Node(name=)

def upload(args):
    root = os.path.abspath(args.icon_directory)
    for (dirpath, dirname, filenames) in os.walk(root):
        for fn in filename:
            path = os.path.join(dirname)

def main(inargs=sys.argv[1:]):
    args = parser.parse_args(inargs)
    upload(args)

if __name__ == '__main__':

    main()
