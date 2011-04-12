#!/usr/bin/env python3

"""
    This file contains some of the useful function which can be re-used
    in other parts of the WedgeUp suite.
"""
__author__="Tinned_Tuna"
__date__ ="$13-Apr-2011 00:51:26$"

import json
import hashlib

# The default configuration file.
default_config = '/etc/wedgeup.conf'

class ConfigError(BaseException):
    pass

class DatabaseError(BaseException):
    pass

def csum(filename, bs=2**20):
    """
        Get the MD5 sum of the given filename.
    """
    md5 = hashlib.md5()
    f = open(filename,'rb')
    while True:
        dat = f.read(bs)
        if not dat:
            break;
        else:
            md5.update(dat)
    f.close()
    return md5.hexdigest()


def decode_json(configp, name):
    """
        Decodes JSON objects out of a given config file.
    """
    try:
        temp = configp.get('DEFAULTS',name)
        temp = json.loads(temp)
    except:
        raise ConfigError("Could not decode "+name)
    return temp


if __name__ == "__main__":
    print ("Hello World")
