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
import os
import zlib

class ConfigError(BaseException):
    pass

class DatabaseError(BaseException):
    pass

def crc(filename):
    """
        Get the CRC value of the file given.
    """
    buff = bytearray()
    for line in open(filename,'rb'):
        for char in line:
            buff.append(char)
    return zlib.crc32(buff)

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

# Read the command line args and the configuration file.

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
try:
    config = configparser.ConfigParser()
    config.read(options.config)
except:
    raise ConfigError("Could not read the config file")

# If the database was not specified, use the one from the command line.
if options.database is None:
    options.database = config.get('DEFAULTS','dblocation')
else:
    raise ConfigError("No database specified")

# Pull out various useful bits of info from the command line.
try:
    disks = decode_json(config,'disks')
except:
    raise ConfigError("Could not read the disks list")

try:
    blacklist = decode_json(config,'blacklist')
except:
    raise ConfigError("Could not read the blacklist")

try:
    root_dir = config.get('DEFAULTS','rootdir')
except:
    raise ConfigError("Could not get the root directory")

try:
    dbloc = config.get('DEFAULTS','dblocation')
except:
    raise ConfigError("Could not get the database location")

# Open the files database.
try:
    filesdb = pickledb.PickleDatabase(dbloc,True,True)
    try:
        filesdb.open()
    except:
        filesdb.create(dbloc)
        filesdb.open(dbloc)
        filesdb['disks']={}
        filesdb['files']={}
        filesdb.commit()
except:
    raise DatabaseError("Error opening the Database.")

# All of the requisite setup is now done. We can move onto walking the fs and
# seeing if anything needs to be copied onto any of the disks.
filelist = {}
os.chdir('/')
print(root_dir)
print("Building File List")
for root, dirs, files in os.walk(root_dir):
    for file in blacklist:
        if file in dirs:
            dirs.remove(file)
    for name in files:
        namepath = os.path.join(root,name)
        filelist[namepath] = {'timestamp': os.stat(namepath).st_mtime\
                             ,'crc32': crc(namepath) \
                             ,'size': os.stat(namepath).st_size }

print(disks)
filesdb['disks']={}
filesdb.commit()
# If the disks aren't listed, list them, and set their currently used space to 0
for disk in disks:
    if disk not in filesdb['disks']:
        filesdb['disks'][disk]={'mountpoint': disks[disk]['mountpoint']\
                               ,'max_size':disks[disk]['size']\
                               ,'current':0\
                                }

filesdb.commit()
print(filesdb['disks'])


# First, order the files by size, largest to smallest. Then the order
# disks -- least space remaining to greatest.
# Put the files which need to be put on the disks on the disks in the first that
# they fit in, if they need to be transfered (i.e. if they've changed or they're
# not listed.

# Ordered files...
all_files = []
for key in filelist:
    all_files.append(key)
file_sorted=sorted(all_files,key=(lambda x : filelist[x]['size']), reverse=True)

# Ordered disks
all_disks = []
for disk in filesdb['disks']:
    all_disks.append(disk)
disks_sorted=sorted(all_disks,key=(lambda x: filesdb['disks'][x]['current']))

