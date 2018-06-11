#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    Blockstack-file
    ~~~~~
    copyright: (c) 2014-2015 by Halfmoon Labs, Inc.
    copyright: (c) 2016 by Blockstack.org
    This file is part of Blockstack-file.
    Blockstack-file is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    Blockstack-file is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    You should have received a copy of the GNU General Public License
    along with Blockstack-file. If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys
import tempfile
import argparse
import socket
import json
import traceback

from ConfigParser import SafeConfigParser
from .version import __version__

import blockstack_client
import blockstack_gpg

APP_NAME = "files"
MAX_EXPIRED_KEYS = 20

log = blockstack_client.get_logger()

if os.environ.get("BLOCKSTACK_TEST", "") == "1":
    # testing!
    CONFIG_PATH = os.environ.get("BLOCKSTACK_FILE_CONFIG", None)
    assert CONFIG_PATH is not None, "BLOCKSTACK_FILE_CONFIG must be defined"

    CONFIG_DIR = os.path.dirname( CONFIG_PATH )

else:
    CONFIG_DIR = os.path.expanduser("~/.blockstack-files")
    CONFIG_PATH = os.path.join( CONFIG_DIR, "blockstack-files.ini" )

CONFIG_FIELDS = [
    'immutable_key',
    'key_id',
    'blockchain_id',
    'hostname',
    'wallet'
]

def get_config( config_path=CONFIG_PATH ):
    """
    Get the config
    """
   
    parser = SafeConfigParser()
    parser.read( config_path )

    config_dir = os.path.dirname(config_path)

    immutable_key = False
    key_id = None
    blockchain_id = None
    hostname = socket.gethostname()
    wallet = None
 
    if parser.has_section('blockstack-file'):

        if parser.has_option('blockstack-file', 'immutable_key'):
            immutable_key = parser.get('blockstack-file', 'immutable_key')
            if immutable_key.lower() in ['1', 'yes', 'true']:
                immutable_key = True
            else:
                immutable_key = False

        if parser.has_option('blockstack-file', 'file_id'):
            key_id = parser.get('blockstack-file', 'key_id' )

        if parser.has_option('blockstack-file', 'blockchain_id'):
            blockchain_id = parser.get('blockstack-file', 'blockchain_id')

        if parser.has_option('blockstack-file', 'hostname'):
            hostname = parser.get('blockstack-file', 'hostname')

        if parser.has_option('blockstack-file', 'wallet'):
