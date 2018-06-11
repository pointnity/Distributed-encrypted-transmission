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
            wallet = parser.get('blockstack-file', 'wallet')
        
    config = {
        'immutable_key': immutable_key,
        'key_id': key_id,
        'blockchain_id': blockchain_id,
        'hostname': hostname,
        'wallet': wallet
    }

    return config


def file_url_expired_keys( blockchain_id ):
    """
    Make a URL to the expired key list
    """
    url = blockstack_client.make_mutable_data_url( blockchain_id, "%s-old" % APP_NAME, None )
    return url


def file_fq_data_name( data_name ):
    """
    Make a fully-qualified data name
    """
    return "%s:%s" % (APP_NAME, data_name)


def file_is_fq_data_name( data_name ):
    """
    Is this a fully-qualified data name?
    """
    return data_name.startswith("%s:" % APP_NAME)


def file_data_name( fq_data_name ):
    """
    Get the relative name of this data from its fully-qualified name
    """
    assert file_is_fq_data_name( fq_data_name )
    return data_name[len("%s:" % APP_NAME):]


def file_key_lookup( blockchain_id, index, hostname, key_id=None, config_path=CONFIG_PATH, wallet_keys=None ):
    """
    Get the file-encryption GPG key for the given blockchain ID, by index.
    if index == 0, then give back the current key
    if index > 0, then give back an older (revoked) key.
    if key_id is given, index and hostname will be ignored
    Return {'status': True, 'key_data': ..., 'key_id': key_id, OPTIONAL['stale_key_index': idx]} on success
    Return {'error': ...} on failure
    """

    log.debug("lookup '%s' key for %s (index %s, key_id = %s)" % (hostname, blockchain_id, index, key_id))
    conf = get_config( config_path )
    config_dir = os.path.dirname(config_path)
    
    proxy = blockstack_client.get_default_proxy( config_path=config_path )
    immutable = conf['immutable_key']

    if key_id is not None:
        # we know exactly which key to get 
        # try each current key 
        hosts_listing = file_list_hosts( blockchain_id, wallet_keys=wallet_keys, config_path=config_path )
        if 'error' in hosts_listing:
            log.error("Failed to list hosts for %s: %s" % (blockchain_id, hosts_listing['error']))
            return {'error': 'Failed to look up hosts'}

        hosts = hosts_listing['hosts']
        for hostname in hosts:
            file_key = blockstack_gpg.gpg_app_get_key( blockchain_id, APP_NAME, hostname, immutable=immutable, key_id=key_id, config_dir=config_dir )
            if 'error' not in file_key:
                if key_id == file_key['key_id']:
                    # success!
                    return file_key

        # check previous keys...
        url = file_url_expired_keys( blockchain_id )
        old_key_bundle_res = blockstack_client.data_get( url, wallet_keys=wallet_keys, proxy=proxy )
        if 'error' in old_key_bundle_res:
            return old_key_bundle_res

        old_key_list = old_key_bundle_res['data']['old_keys']
        for i in xrange(0, len(old_key_list)):
            old_key = old_key_list[i]
            if old_key['key_id'] == key_id:
                # success!
                ret = {}
                ret.update( old_key )
                ret['stale_key_index'] = i+1 
                return old_key

        return {'error': 'No such key %s' % key_id}

    elif index == 0:
        file_key = blockstack_gpg.gpg_app_get_key( blockchain_id, APP_NAME, hostname, immutable=immutable, key_id=key_id, config_dir=config_dir )
        if 'error' in file_key:
            return file_key

        return file_key
    
