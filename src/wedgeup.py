#!/usr/bin/env python3

"""
This is a backup script, WedgeUp.

It is designed to backup systems to a series of drives, also known as 'wedges'.
WedgeUp will only moves files it believes to have been changed. That is, if
their checksum (currently, the MD5) has changed, or their timestamp has been
updated.

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
import hashlib
import shutil
import time

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

def remaining_space(disk):
    """
         Calculate the remaining space on a given disk.
    """
    max_size = int(filesdb['disks'][disk]['max_size'])
    current = int (filesdb['disks'][disk]['current'] )
    return max_size - current


def update_working_space(disk,file):
    """
        Update the space on the in-memory database of the disks:
    """
    filesdb['disks'][disk]['current']+=filelist[file]['size']

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
    filesdb = pickledb.PickleDatabase(dbloc,False,True)
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

print("Building File List...")
for root, dirs, files in os.walk(root_dir):
    for directory in blacklist:

        if os.path.join(root,directory) in dirs:
            dirs.remove(directory)
    for name in files:
        namepath = os.path.join(root,name)
        filelist[namepath] = {'timestamp': os.stat(namepath).st_mtime\
                             ,'csum': csum(namepath) \
                             ,'size': os.stat(namepath).st_size }


# If the disks aren't listed, list them, and set their currently used space to 0
for disk in disks:
    if disk not in filesdb['disks']:
        filesdb['disks'][disk]={'mountpoint': disks[disk]['mountpoint']\
                               ,'max_size':disks[disk]['size']\
                               ,'current':0\
                                }

filesdb.commit()



# First, order the files by size, largest to smallest. Then the order
# disks -- least space remaining to greatest.
# Put the files which need to be put on the disks on the disks in the first that
# they fit in, if they need to be transfered (i.e. if they've changed or they're
# not listed.

# Find which files need copying
files_to_copy = []
for file in filelist:
    if file not in filesdb:
        files_to_copy.append(file)
    else:
        if (filesdb['files'][file]['csum'] != filelist[file]['csum']) or \
           (filesdb['files'][file]['date'] != filelist[file]['date']):
             files_to_copy.append(file)
        else:
            pass


# Ordered disks, no real reason really...
all_disks = []
for disk in filesdb['disks']:
    all_disks.append(disk)
disks_sorted=sorted(all_disks,key=(lambda x: filesdb['disks'][x]['current']))

# Sort the files smallest to largest.
files_sorted = sorted( files_to_copy \
                     , key = (lambda x : filelist[x]['size']) \
                     , reverse = True )

#
# Bin packing algorithm, simple first-fit algo.
#

drives_q = {} # A queue for each disk. Files are queued for each drive.
for disk in disks_sorted:
    drives_q[disk]=[] # Create an empty queue.

non_fitting = [] # The files that cannot be fit onto ANY drives.
# This is where the files are queued.
for file in files_sorted:
    queued = False
    for disk in disks_sorted:
        if filelist[file]['size']<remaining_space(disk):
            # We've found space for the file, queue it.
            drives_q[disk].append(file)
            queued = True
            # Update the used space on the disk
            update_working_space(disk,file)
            # No need to search the other drives, so break out of one loop
            # (the disk-searching loop)
            break
        else:
            # Skip this drive
            pass
    if not queued:
        # We could not fit it on ANY drive, point this out.
         non_fitting.append(file)

# Warn the user if some files would not fit anywhere!
if len(non_fitting) != 0:
    print(\
    "Warning! The following files will NOT be backed up due to lack of space: ")
    print(str(non_fitting))

# Iterate over the disks, putting the queue onto them, and saving a copy of
# the database on the disk.
for disk in drives_q:
    # Request the drive:
    mpoint = filesdb['disks'][disk]['mountpoint']
    print("Please mount "+disk+" at mountpoint " \
         + mpoint +" and hit any key to continue.")
    input()
    for file in drives_q[disk]:
        # Copy the file onto the drive with a nice new name.
        try:
            shutil.copy2(file \
                         , mpoint + '/' + os.path.basename(file) \
                         + str(filelist[file]['csum']))

            filesdb['files'][file]={ 'disk':disk \
                               , 'size':filelist[file]['size'] \
                               , 'csum':filelist[file]['csum'] \
                               , 'modified_time':filelist[file]['timestamp'] \
                               , 'backup_time' : time.localtime() \
                               }
        except:
            print("Could not copy file: "+file)

    # Save the database to the drive!
    curr_time = str(time.time())
    filesdb.commit(mpoint+"/"+"wedgedb-"+curr_time)
    # Save a copy of the config file used
    shutil.copy2(options.config \
                , mpoint+'/'+'wedgecfg' \
                + os.path.basename(options.config)+curr_time)