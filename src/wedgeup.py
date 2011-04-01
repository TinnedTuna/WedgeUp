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

default_config = '/etc/wedgeup.conf'

argparser = optparse.OptionParser(description="A backup tool.", prog="WedgeUp")
argparser.add_option("--config","-c", default=default_config, type="string", \
                      help="""Location of the configuration file, defaults to
                              """+default_config \
                    )
argparser.add_option("--database","-d",type="string", \
                     help="""The location of the database of backed up files.
                             The default is listed in the config file."""
                    )
(options,args) = argparser.parse_args()


config = configparser.ConfigParser()
config.read(options.config)


print(config.get('DEFAULTS','disks'))
