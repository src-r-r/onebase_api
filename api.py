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

import os
import sys
import argparse

from pymongo import MongoClient

from odi_common import settings

client = MongoClient(settings.database())

def main(inargs=sys.argv[0]):
    pass

if __name__ == '__main__':
    main()
