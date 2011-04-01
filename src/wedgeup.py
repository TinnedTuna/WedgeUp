#!/usr/bin/env python3

"""
This is a backup script, WedgeUp.

It is designed to backup systems to a series of drives, also known as 'wedges'.
WedgeUp will only moves files it believes to have been changed. That is, if
their CRC32 has changed, or their timestamp has been updated.

This is kept across runs of each file.

WedgeUp also supports blacklisting of various directories (and all
subdirectories of that directory). For example, /proc should probably not be
backed up, but /home and /var should be.
"""
__author__="Tinned_Tuna"
__date__ ="$01-Apr-2011 15:07:20$"

import optparse
import configparser
import json
import pickledb

class ConfigError():
    pass

def decode_json(configparse, name):
    temp = config.get('DEFAULTS',name)
    temp = json.loads(temp)
    return temp

# The default configuration file.
default_config = '/etc/wedgeup.conf'

# The methods to parse the command line options.
argparser = optparse.OptionParser(description="A backup tool.", prog="WedgeUp")

# An option to modify which configuration file is used.
argparser.add_option("--config","-c", default=default_config, type="string", \
                      help="""Location of the configuration file, defaults to
                              """+default_config \
                    )

# An option to modify where the database is read from.
argparser.add_option("--database","-d",type="string", \
                     help="""The location of the database of backed up files.
                             The default is listed in the config file."""
                    )

# Parse the command line arguments.
(options,args) = argparser.parse_args()


# Read the config file as specified either at the cmd line or by default.
config = configparser.ConfigParser()
config.read(options.config)

# If the database was not specified, use the one from the command line.
if options.database is None:
    options.database = config.get('DEFAULTS','dblocation')
else:
    raise ConfigError("No database specified")



# Pull out various useful bits of info from the command line.
disks = decode_json(config,'disks')
blacklist = decode_json(config,'blacklist')
root_dir = config.get('DEFAULTS','rootdir')
dbloc = config.get('DEFAULTS','dblocation')

# Open the files database.
filesdb = pickledb.PickleDatabase(dbloc,True,True)
filesdb = filesdb.open()

# All of the requisite setup is now done. We can move onto walking the fs and
# seeing if anything needs to be copied onto any of the disks.
