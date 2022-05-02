#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Phuong Tran, Joseph Tarango
# *****************************************************************************/
"""
bufdata implements interface(s) for working with Twidl buffers;
Primarily used and maintained by NSG's Test Firmware Team.

Please talk to CS or the current maintainer before making
modifications to this file.

"""
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from builtins import (bytes, str, open, super, range, zip, round, input, int, pow, object)
#Script version maintained using hgMaintenance.py
#$REVISION$
__version__ =  'bufdata.py          :Chris Smerz         :2010-08-05 11:54:21'

import os, sys
import datetime

################################################################################################################
################################################################################################################

class BufData:
    """
    BufData - Abstract class for data structures that move information
    to/from Twidl buffers. Due to the \"Figure out what to do at runtime\"
    nature of python, it's not necessary to implement an interface, save to
    have the inheriting classes break constantly and/or
    reference this doc work. Inheriting from this class helps developers
    in TFW Twidl to code in a consistent fashion.

    BufData classes should NOT be responsible for drive interface or
    population of the buffers they will work with without a well
    documented reason to do so. The reason for this are:
    - Tools to populate the buffer may be volatile (Twidl, Firmware), the
      tools to manipulate the data from the drive need not be.
    - As BufData classes are able to work from files, it is possible and
      desirable to work with them in a Non-Twidl Environment. This includes but
      is not limited to debug away from drives and data analysis of
      information from the manufacturing process.

    """

    name = None             #name that may be used by a class if desired.
    last_file = None        #last file accessed (read or write)
    last_file_stat = None   #os.stat from the last file accessed. See os.stat() for usage

    def __str__(self):
        """
        Inclusion of str is almost unnecessary, save to remind developers
        that BufData classes are expected to be able to be string-ed
        in normal use.

        """
        raise NotImplementedError
        return ''

    def from_buf(self, myBuf, offset=0):
        """
        Extracts information from  \'myBuf' starting at \'offset\'.

        myBuf contains an iterable + indexable object, typically a
        Twidl buffer, which contains the information to be parsed.

        offset is the location from which the class will start to
        extract data.

        It is typical to see this optionally called from __init__,especially
        on classes that extract data that is read to a buffer from drive

        <Historical Note> Parameter order  is inverted from old TFW Twidl
        code; will require refactor as it's implemented. Adoption of
        PEP 8 naming conventions by this class do the same.

        """
        raise NotImplementedError
        return

    def to_buf(self, myBuf, offset=0):
        """
        Injects information to \'myBuf' starting at \'offset\'.

        myBuf contains an iterable + indexable object, typically a
        Twidl buffer, where class information will be inserted.

        offset is the location from which the class will start to
        insert data.

        <Historical Note> Parameter order is inverted from old TFW Twidl
        code; will require refactor as it's implemented.  Adoption of
        PEP 8 naming conventions by this class do the same.

        """
        raise NotImplementedError
        return

    def byte_size(self):
        """
        Return the number of bytes (int) this uses in a buffer.

        <Historical Note> Previous implementation in TFW Twidl set this as
        an attribute; will require refactor as it's implemented.  Adoption
        of PEP 8 naming conventions by this class do the same.

        """
        raise NotImplementedError
        return 0

    def from_file(self, file_name, offset=0):
        """
        Loads binary information from \'file_name\'.

        Implementation compatible with \'to_file\'.

        """
        fileobj =  open(file_name,'rb')
        raw_data = fileobj.read()
        fileobj.close()

        faux_buf =[ord(x) for x in raw_data]
        self.from_buf(faux_buf, offset)

        self._update_file_info(file_name)
        return

    def to_file(self, file_name, offset=0, append=False):
        """
        Saves information to \'file_name\' in binary format.

        Implementation compatible with \'from_file\'.

        """
        #code initially from Intel/vendspec.rdump() by Sandeep Ramannavar
        faux_buf =  [0 for x in range(self.byte_size()+offset) ]
        self.to_buf(faux_buf,offset)

        s = "".join([chr(x) for x in faux_buf])

        if(append) : fileobj = open(file_name, mode = 'wb+')
        else       : fileobj = open(file_name, mode = 'wb')

        fileobj.write(s)
        fileobj.close()

        self._update_file_info(file_name)
        return

    def append_to_file(self, file_name, offset = 0):
        """
        Saves additional information to \'file_name\' in binary format.

        Implementation compatible with \'to_file\'.

        Most bufdata/dataparse implementations won't make much use of this.
        The only known one so far is burn-in log,
        which is simply an endless stream of repeating elements: log records.

        """
        self.to_file(file_name=file_name, offset=offset, append=True)

    def txt_to_file(self, file_name):
        """
        Saves string representation of information to file.

        No mirroring 'from txt', as this would require all classes
        implement and maintain a text parser; which is non-trivial.

        """
        s = str(self)
        fileobj = open(file_name, mode = 'w')
        fileobj.write(s)
        fileobj.close()
        return

    def file_info(self):
        """
        Returns a sting containing the file name,
        created datetime, and file size,

        returns '' if object never accessed a file.
        """
        if (self.last_file == None) or (self.last_file_stat == None):
            return ''

        file_info_string = ''
        file_info_string += 'F:%s'%self.last_file
        file_info_string += ' C:%s'%(str(datetime.datetime.fromtimestamp(self.last_file_stat.st_ctime)))
        #file_info_string += ' M:%s'%(str(datetime.datetime.fromtimestamp(self.last_file_stat.st_mtime)))
        file_info_string += ' S:%d'% (self.last_file_stat.st_size)

        return file_info_string

    def _update_file_info(self, file_name):
        """
        Update the maintained file information.

        Not intended for public use.

        """
        self.last_file = file_name
        self.last_file_stat = os.stat(file_name)
        return

    def similar(self, other):
        """
        Check if....

        -'other' is 'None'
        -'other' is not a bufdata class
        -byte_size of other does not match bytesize of self

        Each of these conditions will cause similar to return False.
        Else, returns True.

        Used by:
            __eq__
            __ne__
            bits_different
        ...in this class.

        """
        if other == None:
            return False

        if not isinstance(other, BufData):
            return False

        if not (self.byte_size() == other.byte_size()):
            return False

        return True

    def __eq__(self, other):
        """
        Binary compare (to_buf representation) of this to other.

        Checks for similar before comparing.
        Returns false if 'self' and 'other' are not similar().

        """
        if not self.similar(other):
            return False

        self_buf = [0 for x in range(self.byte_size())]
        other_buf = [0 for x in range(other.byte_size())]

        self.to_buf(self_buf)
        other.to_buf(other_buf)

        if self_buf != other_buf:
            return False

        return True

    def __ne__(self, other):
        """Not self.__eq__(other) """
        return not self.__eq__(other)

    def bits_different(self, other):
        """
        Compares this bufdata structure to 'other'.

        Returns the number of bits that differ between the 2.

        Raises Exception if similar() is false. There's no good way
        to report that the comparison could not be made.

        Check similar if you're concerned about breaking in this manner

        Note that this can be a very time-expensive operation.

        """
        if not self.similar(other):
            raise (Exception, 'bits_different() requires self and other to be similar()')

        byteCount = self.byte_size()

        self_buf = [0 for x in range(byteCount)]
        other_buf = [0 for x in range(byteCount)]

        self.to_buf(self_buf)
        other.to_buf(other_buf)

        bitsDifferentCount = 0

        for byte in range(byteCount):
            if self_buf[byte] != other_buf[byte]:
                #Borrowed from 'rawdata' in tfw (old bufdata implementation)
                #by yours truly, -cs
                #xor the bits and tally them.
                diff = self_buf[byte]^ other_buf[byte]
                for x in range(8):
                    bitsDifferentCount += diff & 1
                    diff = diff >> 1
        # print '>>>>> debug bufdata.bits_different  bitsDiffrentCount: %d'%(bitsDifferentCount)
        return bitsDifferentCount

    def isAllFFs(self):
        """
        checks to see if all the data as represented
        in the buffer is all 0xFF.

        Useful, as erased nand is 0xFF


        """
        f_array = [0xFF for x in range(self.byte_size())]
        my_data = [0 for x in range(self.byte_size())]

        self.to_buf(my_data)

        return my_data == f_array


class DirectAccess(BufData):
    """
    Inheriting class of bufdata that provides a standardized interface
    to a data member. Currently used to provide BufDataList.member
    access to BufDataList.

    """

    #This goes away becomes instance check
    #_bufdatalist_direct_access = False #changes the get/set behavior
                                       #in a BufDataList
    _value = None                      #used by _bufdatalist_direct_access

    def __init__(self):
        pass

    def get_direct_access(self):
        """
        Interface to the information stored in an direct access bufdata class.

        """
        #if not self._bufdatalist_direct_access:
        #    raise NotImplementedError, 'Class is not a direct access class'

        return self._value

    def set_direct_access(self, value):
        """
        Interface to the information stored in an direct access bufdata class.

        """
        #if not self._bufdatalist_direct_access:
        #    raise NotImplementedError, 'Class is not a direct access class'

        self._value = value
        return


class BufDataList(BufData):
    """Ordered list of BufData that implement the BufData interface.

    in combination with \'endian\' module; should make 'BufferDataDecode'
    obsolete; though it is not incompatible. Compatibility is achieved from
    the common interface, BufData.
    """
    _buf_list = None

    def __init__(self):
        self.__dict__['_buf_list'] = []

    def __str__(self):
        delimiter = '\r\n'
        a_str = ''
        for member in self._buf_list:
            a_str+= str(member)+delimiter
        return a_str

    def from_buf(self, myBuf, offset=0):
        """
        Extracts listdata from a buffer.

        See bufdata.BufData (super class) for detail.

        """
        buf_idx = offset
        for bd in self._buf_list:
            bd.from_buf(myBuf, buf_idx)
            buf_idx += bd.byte_size()
        return

    def to_buf(self, myBuf, offset=0):
        """
        Inserts list data in to a buffer.

        See bufdata.BufData (super class) for detail.

        """
        buf_idx = offset
        for bd in self._buf_list:
            # print ">>>> debug bufdata buf_idx: %d  bd.byte_size: %d" % (buf_idx, bd.byte_size() )
            bd.to_buf(myBuf, buf_idx)
            buf_idx += bd.byte_size()
        return

    def byte_size(self):
        """
        Reports data size in bytes in buffer.

        See bufdata.BufData (super class) for detail.

        """
        size = 0
        for bd in self._buf_list:
            size +=bd.byte_size()
        return  size

    def __iter__(self):
        return iter (self.__dict__['_buf_list'])

    def __getitem__(self, index):
        """Returns the item from the ordered list at 'index'."""
        return self._buf_list[index]

    def __len__(self):
        """
        Returns the number of things in the ordered list; not to be
        confused with \'byte_size\'.

        """
        return len(self._buf_list)

    def append(self, member, name=None):
        """
        Adds a member to this ordered list.

        If a name is provided, member is made accessible as an attribute.

        """
        self._buf_list.append(member)

        if name != None:
            member.name = name
        return

    def __getattr__(self, parameter):
        """
        Attribute access to list members that were named when added.

        If _bufdatalist_direct_access is enabled, returns _value for the
        contained data.

        """
        # print '>>>>debug bufdata.__getattr__ my name is %s'%(self.name)
        # print '>>>>debug bufdata.__getattr__ i seek %s'%(parameter)
        value_in_buf_list = False
        for member in self.__dict__['_buf_list']:
            # print '>>>>debug bufdata.__getattr__ '+member.name+'|' +'%s'%(str(member.name == parameter))
            if member.name == parameter:
                value_in_buf_list = True
                #if member.is_direct_access():
                if isinstance(member, DirectAccess):
                    return_value = member.get_direct_access()
                else:
                    return_value = (member)
                    # print '>>>>debug bufdata.__getattr__ <%s>'%(str(type(return_value)))
                break

        if not value_in_buf_list:
            if self.__dict__.has_key(parameter):
                return_value = self.__dict__[parameter]
            else:
                raise (AttributeError, 'Parameter not found: %s'%(parameter))

        return return_value

    def __setattr__(self, parameter, value):
        """
        Attribute access to list members that have \'member_name\' assigned.

        If _bufdatalist_direct_access is enabled, sets _value for the
        contained data.

        BE CAREFUL IF YOU'RE SETTING NON-DIRECT ACCESS MEMBERS. IT ASSIGNS
        THE LIST MEMBER.

        """
        value_in_buf_list = False
        for member in self.__dict__['_buf_list']:
            if member.name == parameter:
                value_in_buf_list = True
                #if member.is_direct_access():
                if isinstance(member, DirectAccess):
                    member.set_direct_access(value)
                else:
                    member = value

        if not value_in_buf_list:
            self.__dict__[parameter] = value

        return

    def base_str(self):
        '''over-rides user implemented string functions'''
        return BufDataList.__str__(self)
