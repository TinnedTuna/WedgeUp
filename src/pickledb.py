#!/usr/bin/env python3

import pickle
import random
import hashlib

"""
An on-disk database hacked together using the Pickle module.

Fast, once the database is loaded into memory, and supports any Python object.

Key/Value store, only restriction is that the Key MUST be hashable.
"""

__author__="Tinned_Tuna"
__date__ ="$01-Apr-2011 16:19:33$"


class PVerficationError(BaseException):
    pass

class PVerficationFalse(BaseException):
    pass

class PKeyNotFound(BaseException):
    pass

class PNoDatabaseGiven(BaseException):
    pass

class PDatabaseAlreadyOpen(BaseException):
    pass

class PDatabaseNotOpen(BaseException):
    pass

class PickleDatabase():
    """
        The database class, this handles everything.
    """
    def __init__(self, filehand=None, commit_on_change=None, verification=None):
        """
            Return a new object ready for the day.
        """
        if verification is None:
            self.verif = True
        else:
            self.verif = False
        if commit_on_change is None:
            self.autocommit = True
        else:
            self.autocommit = False

        if filehand is None:
            self.fileh = None
        else:
            self.fileh = filehand
        self.opened = False

    def open(self, filehand=None):
        """
            Open a given database.
        """
        # Raise an error if you're trying to open an already open database.
        if self.opened == True:
            raise PDatabaseAlreadyOpen()

        # Faffing with the arguments to get the header file.
        if (filehand is None) and (self.fileh is None):
            raise PNoDatabaseGiven()
        else:
            if filehand is not None:
                self.fileh = filehand 
            # Load the header file.
            headhand = open(self.fileh,'rb')
            self.header = pickle.load(headhand)
            headhand.close()
            # Verify it.
            if self.__verify(self.header):
                # Load the database into memory.
                datahand = open(self.header['data'],'rb')
                self.data = pickle.load(datahand)
                datahand.close()
                self.opened = True
                return True
            else:
                raise PVerficationFalse()

    def __md5(self, filename, bs=2*20):
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
        return md5.digest()
        
        
    def __verify(self, header=None):
        """
            Verify a database datafile. Uses md5sum
        """
        # If verification is turned not turned on, just assume it's true
        if not self.verif:
            return True
        # Check we have an argument.
        if header is None:
            raise PVerificationError()
        try:
            md5file = self.__md5(header['data'])
            if str(md5file) == str(header['md5sum']):
                return True
            else:
                return False
        except:
            raise PVerficationError()

    def __getitem__(self, key=None):
        """
            Retrieve an item from the database
        """
        if key is None: 
            raise PKeyNotFound()
        if self.opened == False:
            raise PDatabaseNotOpen()
        else:
            return self.data[key]

    def __setitem__(self, key=None, value=None):
        """
            Retrieve an item from the database
        """
        if key is None: 
            raise PKeyNotFound()
        if self.opened == False:
            raise PDatabaseNotOpen()
        else:
            self.data[key] = value
        if self.autocommit:
            self.commit()

    def __commit_loc(self,loc):
        """
            Commit changes to the database to a given location, loc.
        """
        local_data=loc+str(random.randint(0,100000000000))+'.pdata'

        # Write the datachunk then update the header.
        datahandle = open(local_data,'wb')
        pickle.dump(self.data, datahandle)
        datahandle.close()


        # Get the new md5sum
        newmd5 = self.__md5(local_data)
        # Create & update the local header file.
        local_header = self.header
        local_header['md5sum'] = newmd5

        # Write it out.
        headerhandle = open(loc, 'wb')
        pickle.dump(local_header, headerhandle)
        headerhandle.close()

    def commit(self,loc=None):
        """
            Commit all the changes to the database.

            The optional loc parameter allows the user to save this database
            to a different location.
        """
        if loc is not None:
            self.__commit_loc(loc)
            return

        # Write the datachunk then update the header.
        datahandle = open(self.header['data'],'wb')
        pickle.dump(self.data, datahandle)
        datahandle.close()
        
        # Get the new md5sum
        newmd5 = self.__md5(self.header['data'])
        # update the header file.
        self.header['md5sum'] = newmd5 

        # Write it out.
        headerhandle = open(self.fileh, 'wb')
        pickle.dump(self.header, headerhandle)
        headerhandle.close()

    def create(self, filename):
        """
            Create a new, empty database.
        """
        data = {}
        dataname = filename+str(random.randint(0,100000000000))+'.pdata'

        dhandle = open(dataname,'wb')
        pickle.dump(data, dhandle)
        dhandle.close()

        header = {}
        header['md5sum'] = self.__md5(dataname)
        header['data'] = dataname
        
        hhandle = open(filename,'wb')
        pickle.dump(header,hhandle)

    def __contains__(self,key):
        """
            Return True if a key is in the database, False if it is not and
            raise an exception if the database is not open.
        """
        if not self.opened:
            raise PDatabaseNotOpen()
        else:
            return (key in self.data)
        hhandle.close()

    def __iter__(self):
        """
            Iterate over the keys. whoop... ¬.¬
        """
        if not self.opened:
            raise PDatabaseNotOpen()
        for key in self.data:
            yield key

        
