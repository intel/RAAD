#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Phuong Tran, Joseph Tarango
# *****************************************************************************/
"""
Base classes for buffer dictionaries and lists.

    bufdict - Hold a single structure or entry within a buflist.
    buflist - Holds a header, list of bufdict objects and optional tail.

These should be inherited to create your own subclasses for buffer data.
See dataparse\mrr.py for example code that uses these.
I will refer to code from dataparse\mrr.py in this documentation.

################################################################################
bufdict - Container for a single structure of data.

bufdict is much like a python dictionary with the following differences.

    Fixed set of ordered keys defined by you when you inherit the class.
    Data can be accessed as attributes or with the keys.
    Customized printing styles for each data member.
    Help strings for each data member.

    Supports relevant, expected methods:

    help()      - Show the data members and a description.
    str()       - Get a string of the class (used for printing).
    bytesize()  - Total bytes of buffer space used.
    tobuf()     - Send contents to a buffer for writing to a drive.
    frombuf()   - Pull contents from a buffer that was read from a drive.
    tofile()    - Saves binary contents to a filename or file object.
    fromfile()  - Pulls binary contents from a filename or file object.
    txttofile() - Sends human readable content to a filename or file object.

Each class derived from bufdict requires a description of contents.
A description list holds the following info for each data member:

    bdNAME  - Field name: Key to the dictionary of values.
    bdSIZE  - Field size in bits.
    bdSIGN  - Boolean flag for signed or not.
    bdINIT  - Default Value.
    bdSTYLE - Print style for the field. (See styles below.)
    bdTOKEN - Token dictionary for the field (or None).
    bdHELP  - Help String for the field.

I'll use the mrr.config class in mrr.py to demonstrate...
This list describes the contents of the mrr.config class.
The contents exactly match that of the FW MRR Config structure.

MRR_CONFIG_DESCRIPTION = \
[
####  name    size signed      default  style  Tokens  help string
    'version',  16,     0, MRR_VERSION, bdHEX,  None, "MRR Version Number",
    'size',     16,     0,          36, bdDEC,  None, "Size of the structure in bytes.",
    'enabled',  32,     0,           0, bdBOOL, None, "Use MRR or not (boolean).",
    'nudge',    32,     0,           0, bdBOOL, None, "Use nudges or not on excessive bit errors (boolean).",
    'spiral',   32,     0,           0, bdBOOL, None, "Use spiral search on mixed page reads (boolean).",
    'first',    32,     0,           0, bdBOOL, None, "Use spiral search on all blind searches (boolean).",
    'resetrlp', 32,     0,           1, bdBOOL, None, "Put RLP back to 0mV offset when mrr finishes (boolean).",
    'step',     32,     0,           4, bdDEC,  None, "Reference step size during nudge. Tens of mV. 0-150mV in 10mV steps.",
    'cycle',    32,     0,           0, bdDEC,  None, "Cycle count to start doing MRR.",
    'thresh',   32,     0,           8, bdDEC,  None, "Correctable error threshold to trigger a nudge.",
]

Available print styles:

    bdHEX     - Print value in hex
    bdDEC     - Print value in decimal
    bdBOTH    - Print value in both hex and decimal
    bdBOOL    - Print value as True or False
    bdSTR     - Print value as string.
    bdBCD     - Print value in binary coded decimal.
    bdNONE    - Print nothing (for reserved, unused entries)

You can also specify a dictionary of tokens for each field. Without tokens,
the values are passed as ordinary numbers. If you specify a token dictionary
for a field the token strings will print instead of the numbers.
The string token names can also be used to pass in values.
The mrr.refs class is a simple example. The ref offset values are mostly
signed integers but there is one tokenized value, 0xFF00, which
means "do not change" when passed to the SSD. Here's the code...

    ## Tokenize the "Do Not Change" value for ref offsets.
    REF_TOKENS = {'DNC' : 0xFF00}

    ## A set of reference offsets for one die.
    MRR_REFS_DESCRIPTION = \
    [
        'die',  16, 0,     0, bdDEC,       None, "Logical die number",
        'rlp',  16, 1, 'DNC', bdDEC, REF_TOKENS, "Lower page read ref when UP is not programmed.",
        'rslc', 16, 1, 'DNC', bdDEC, REF_TOKENS, "SLC page read. Needed for 1.5b/c L74 parts.",
        'r1',   16, 1, 'DNC', bdDEC, REF_TOKENS, "Also known as r01. For Upper page between L0 & L1.",
        'r2',   16, 1, 'DNC', bdDEC, REF_TOKENS, "Also known as r00. For lower page between L1 & L2.",
        'r3',   16, 1, 'DNC', bdDEC, REF_TOKENS, "Also known as r10. For Upper page between L2 & L3.",
    ]

The above code also shows the token string being used as the default value.

The description list is used to when constructing the class.
Here's a simplified version of mrr.config showing how...

    class config(bufdict): # <-- Inherit bufdict

      def __init__(self, filename=None, buf=None, other=None):

        bufdict.__init__(self, description=MRR_CONFIG_DESCRIPTION, version=MRR_VERSION,
                            name="MRR Config", filename=filename, buf=buf, other=other)

The above is ALL that's needed to make a functional class.
Inherit bufdict and call bufdict's constructor from your constructor.

Note that the constructor can accept a filename, buf or other class.
At the time you create an object, it can load from a file, buf or some
other object with proper contents.

In order to make your class a bit more user-friendly, consider
including your data members in the constructor and create a 'set' method.
Here's the full mrr.config class that does so...

    class config(bufdict):

      def __init__(self, filename=None, buf=None, other=None,
                 enabled=None, nudge=None, spiral=None, first=None,
                 resetrlp=None, step=None, cycle=None, thresh=None):

        bufdict.__init__(self, description=MRR_CONFIG_DESCRIPTION, version=MRR_VERSION,
                            name="MRR Config", filename=filename, buf=buf, other=other)

        self.set(enabled=enabled, nudge=nudge, spiral=spiral, first=first,
                 resetrlp=resetrlp, step=step, cycle=cycle, thresh=thresh)

      def set(self, enabled=None, nudge=None, spiral=None, first=None,
                 resetrlp=None, step=None, cycle=None, thresh=None):
        "Set contents all at once"
        if(enabled  != None) : self.enabled  = enabled
        if(nudge    != None) : self.nudge    = nudge
        if(spiral   != None) : self.spiral   = spiral
        if(first    != None) : self.first    = first
        if(resetrlp != None) : self.resetrlp = resetrlp
        if(step     != None) : self.step     = step
        if(cycle    != None) : self.cycle    = cycle
        if(thresh   != None) : self.thresh   = thresh

The above code enables users to fill data members when the object is
created or directly set multiple values at once with the set method:

#    >>> from dataparse import mrr
#    >>> c = mrr.config(enabled=1)
#    >>> c
    MRR Config:
             version   0x0105
                size       36
             enabled     True
               nudge    False
              spiral    False
               first    False
            resetrlp     True
                step        4
               cycle        0
              thresh        8
#
#    >>> c.set(enabled=0, step=6, thresh=4)
#    >>> c
    MRR Config:
             version   0x0105
                size       36
             enabled    False
               nudge    False
              spiral    False
               first    False
            resetrlp     True
                step        6
               cycle        0
              thresh        4


Normal python help does not show the individual data members because
they are created at run time. So, bufdict has a help method to describe
the contents. The help strings come from your description list.
Here's the mrr.config example:

#    >>> from dataparse import mrr
#    >>> c = mrr.config()
#    >>> c.help()
    MRR Config contains the following:
               version - MRR Version Number
                  size - Size of the rest of the structure in bytes.
               enabled - Use MRR or not (boolean).
         nudge_enabled - Use nudges or not on excessive bit errors (boolean).
        spiral_enabled - Use spiral search on mixed page reads (boolean).
          spiral_first - Use spiral search on all blind searches (boolean).
             reset_rlp - Put RLP back to 0mV offset when mrr finishes (boolean).
            nudge_step - Reference step size during nudge.
           cycle_count - Cycle count to start doing MRR.
            ecc_thresh - Correctable error threshold to trigger a nudge.

The data members can be accessed as attributes or the class can behave
like a dictionary. Sticking with the mrr.config example:

#    >>> c.enabled
    True
#    >>> c['enabled']
    True

The data members are also ordered, unlike a regular dictionary.
When you iterate over bufdict classes the data members will always come out
in the same order as they are in the description list. As such,
bufdict classes behave as an ordered dictionary with a fixed set of keys:

#    >>> for key in c: print "%10s" % key, c[key]
    ...
       version 261
          size 36
       enabled False
         nudge False
        spiral False
         first False
      resetrlp True
          step 4
         cycle 0
        thresh 8

Since bufdict is fundamentally a dictionary, standard methods will work.

#    >>> c.keys()
    ['version', 'size', 'enabled', 'nudge', 'spiral', 'first',
    'resetrlp', 'step', 'cycle', 'thresh']
#    >>> c.values()
    [261, 36, 0, 0, 0, 0, 1, 4, 0, 8]
#    >>> c.items()
    [('version', 261), ('size', 36), ('enabled', 0), ('nudge', 0),
    ('spiral', 0), ('first', 0), ('resetrlp', 1), ('step', 4),
    ('cycle', 0), ('thresh', 8)]
#    >>> c.has_key('crap')
    False
#    >>> c.has_key('size')
    True

Also, bufdict has a bit more info for each data member.
That info can be extracted as well...

#    >>> c.bitsizes()
    [16, 16, 32, 32, 32, 32, 32, 32, 32, 32]
#    >>> c.defaults()
    [261, 36, 0, 0, 0, 0, 1, 4, 0, 8]

################################################################################
bufarray - Holds the combination of a bufdict and a python bytearray.

A bufarray inherits directly from a bufdict and python bytearray, so it's quite
literally a combination of both. You will make a bufarray in exactly the same
way described above for bufdict. The basic use case is when the buffer
interaciton with the device has a structured header (the bufdict part) followed
by a bytearray. Then in twidl you will manipulate the object exactly the same as
you would a bytearray.

The only thing you really need to know is that you should specify a size for the
bytearray during construction. The first parameter to the constructor is the
size of the bytearray.

################################################################################
buflist - Holds a header and a list of identical bufdict objects.

buflist is a container for multiple, identical bufdict objects.

The presumption is that a given NLBA will send or receive a header
followed by a variable number of identical structures. This may not be true
for all the NLBAs, but perhaps most...

The header is itself a bufdict class and every entry will be an instance of
a different bufdict class. As such, you must first create the bufdict
classes for the header and the entries (and a tail if needed).

All the MRR NLBAs use the same header, so there is a single header class
defined in dataparse\mrr.py. Yours may be different, of course.
The header MUST contain a "size" since we must know how many entries.
Any NLBA with variable entries will provide a size in it's header.

    MRR_HEADER_DESCRIPTION = \
    [
      'version', 16, 0, MRR_VERSION, bdHEX, None, "MRR Version Number",
      'size',    16, 0,           0, bdDEC, None, "Number of entries in the list.",
    ]

    class header(bufdict):
        def __init__(self, namesize=18, valuesize=10):
            bufdict.__init__(self, description=MRR_HEADER_DESCRIPTION,
            version=MRR_VERSION, namesize=namesize, valuesize=valuesize)

The above fully defines the header class. Nothing else is needed.

"version" passed to the constructor is optional and enables version checking.
If you specify a version number, it will be checked against the actual
version from the SSD when the header is read.

The optional namesize and valuesize parameters specify the size of the
fields to use when printing. This gives you some flexibility in customizing
printing without needing to override the __str__ method. Of course, for fully
custom printing, feel free to override __str__ if you want. See the
mrr.refs and mrr.log classes for more alternate string examples.

Next, you need a bufdict class for each entry in your buflist:

    YOUR_DESCRIPTION = \
    [
        'enabled', 32, 0, 0, bdDEC, None, "Use MRR or not (boolean).",
        'nudge',   32, 0, 0, bdDEC, None, "Use nudges or not (boolean).",
    ]

Each of the members above are 32 bits long, unsigned, default to 0, will
print in decimal format and have a help string.

Then your entry class will inherit from bufdict and have an __init__() method.
At it's simplest, all you need to do is call bufdict.__init__():

    class yourclass(bufdict):
        def __init__(self):
            bufdict.__init__(self, description=YOUR_DESCRIPTION, name="Name")

Finally, you make your buflist class...
Your list class inherits buflist and must supply the header class
and the class for each entry. All the entries will be of the same class.
Here's a simple example making a list using your own header.

    class yourlist(buflist):
        def __init__(self):
            buflist.__init__(self, entryclass=yourentry,
                                   headerclass=yourheader,
                                   name="My List")

The buflist objects always behave like a list and all the relevant methods
of a list are supported. Slicing works well, for example...
"""

from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from builtins import (bytes, str, open, super, range, zip, round, input, int, pow, object)

import operator
import sys
import math
import binascii
from ctypes import *
from array import *
from pprint import *

################################################################################################################
################################################################################################################

# Fields in the description lists.
from xlrd import colname

bdNAME = 0  ##< Field name: Key to the dictionary of values.
bdSIZE = 1  ##< Field size in bits.
bdSIGN = 2  ##< Boolean flag for signed or not.
bdINIT = 3  ##< Initial Value.
bdSTYLE = 4  ##< Print style for the field. (See styles below.)
bdTOKEN = 5  ##< Token dictionary (or None)
bdHELP = 6  ##< Help String for the field.
bdFIELDS = 7  ##< Number of fields for the descriptions. KEEP LAST


def long(value):
    return int(value)


# Classes for handling the print styles for each value are below.
# These encapsulate conversion of values to/from strings.
# These do not hold the values themselves. Only string conversion methods.
# The derived print styles below, in general, only need to overload the getString() method.
# In all ordinary cases, only need to alter the default parameter values of getString().

## Bass class for print styles. Inherently knows how to do hex.
## Please use "bdXXXX" names for the derived classes.
class bdPrintStyle(object):
    "Supports display styles."

    def __init__(self, bits=32, signed=False, tokens=None):
        self.tokens = tokens
        self.bits = bits
        self.signed = signed
        self.hexDigits = int(math.ceil(float(bits)) / 4.0)
        self.hexFormat = "0x%%0%dX" % self.hexDigits
        self.strSize = int(math.ceil(float(bits)) / 8.0)
        self.strFormat = "%%%ds" % self.strSize

    # Display some information about the class.
    # Not intended to be overloaded when inherited.
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "Bufdict Print Style %s, %d bits, Bool:%s, String:%s" % (self.getStyle(), self.bits, self.isBool(), self.isString())

    # Returns the name of the class.
    def getStyle(self):
        return self.__class__.__name__

    # Some code reacts differently if the type is boolean.
    # Overload this to return True in boolean print styles.
    def isBool(self):
        return False

    # Some code reacts differently if the type is a string.
    # Overload this to return true in string print styles.
    def isString(self):
        return False

    # Some data members are not used and not displayed.
    # Overload this to return False if it should not be displayed.
    def isDisplayed(self):
        return True

    # This requires a value to be passed, so is not implemented as __str__.
    # This is expected to be over-ridden when inherited to alter behavior.
    def getString(self, value, useHex=True, skipTokens=False, valueSize=None):
        "Convert value to a string."

        if skipTokens != True:
            t = self.token(value)
        else:
            t = None

        if t != None:
            s = t
        elif useHex == True:
            s = self.hexFormat % value
        elif self.isBool():
            s = str(value != 0)
        else:
            s = str(value)

        # Strings are strictly sized.
        if self.isString():
            s = s[:self.strSize]
            s = self.strFormat % s
            s = "'" + s + "'"

        if valueSize != None:
            valueformat = "%%%ds" % valueSize
            s = valueformat % s

        return s

    ## Check the maximum string size that could be returned.
    def maxStringSize(self):
        # create maximal value for the field.
        if self.isString():
            value = "x" * self.strSize
        else:
            value = - ((1 << self.bits) - 1)

        l = len(self.getString(value))

        # Now check all the tokens.
        if self.tokens != None:
            for k in self.tokens:
                if (len(k) > l): l = len(k)

        return l

    def token(self, value):
        "Return the token string for a value or None if no token exists."
        if self.tokens != None:
            for t in self.tokens:
                if self.tokens[t] == value:
                    return t
        return None

    def detoken(self, value):
        "Detokenize a value (change a token string to a number)."
        if self.tokens != None and self.tokens.has_key(value):
            return self.tokens[value]

        # Is it a string?
        if isinstance(value, str):
            # Boolean?
            if str(value) == 'True' or str(value) == 'true':
                value = 1
            elif str(value) == 'False' or str(value) == 'false':
                value = 0

            # Is it hex? (Must start with 0x and then be hex digits)
            elif len(value) > 2 and value[0] == '0' and (value[1] == 'x' or value[1] == 'X'):
                try:
                    value = long(value[2:], 16)
                    return value
                except:
                    pass

            # One last try using decimal conversion.
            try:
                value = long(value)
            except:
                pass

        # Strings are strictly sized.
        if self.isString():
            value = str(value)[:self.strSize]

        return value

    def extractValue(self, rawInteger, NSGstring=True):
        "Extract the value from a raw integer created from a buffer"

        mask = 1 << self.bits

        # String?
        if self.isString():
            mystring = ''
            # SSD's store two characters per 16b integer in strings.
            # These need to be reversed to make it an ordinary C-style character array.
            # I have no idea why NSG SSDs store strings this way.
            if NSGstring:
                while rawInteger != 0:
                    second_character = chr(rawInteger & 0xff)
                    rawInteger = rawInteger >> 8
                    first_character = chr(rawInteger & 0xff)
                    rawInteger = rawInteger >> 8
                    mystring += first_character + second_character
            # Normal string of characters in the intuitive, non-NSG order.
            else:
                while rawInteger != 0:
                    mystring += chr(rawInteger & 0xff)
                    rawInteger = rawInteger >> 8

            value = mystring

        # Signed value?
        elif self.signed and rawInteger >= (mask >> 1):
            value = long(rawInteger - mask)

        # Ordinary value?
        else:
            value = long(rawInteger)

        return value

    def makeRawInteger(self, value, NSGstring=True):
        "Convert a value into raw integer format on the way to a buffer"

        # String types need conversion to integer.
        if self.isString():

            # idiot proof.
            value = str(value)
            i = 0
            l = len(value)

            # SSD's store two characters per 16b integer in strings.
            # These need to be reversed to make it an ordinary C-style character array.
            # I have no idea why NSG SSDs store strings this way.
            if NSGstring:
                while l >= 2:
                    l -= 1
                    second_byte = ord(value[l])
                    l -= 1
                    first_byte = ord(value[l])
                    i = (i << 8) | first_byte
                    i = (i << 8) | second_byte

            # Ordinary string is in an intuitive order.
            else:
                while l >= 1:
                    l -= 1
                    i = (i << 8) | ord(value[l])

            value = i

        mask = (1 << self.bits) - 1
        return long(value & mask)


# The derived, specific print styles follow...

class bdHEX(bdPrintStyle):
    "Supports hexadecimal print style, including hex dumps"

    def getString(self, value, useHex=True, skipTokens=False, valueSize=None):
        return bdPrintStyle.getString(self, value, useHex=useHex, skipTokens=skipTokens, valueSize=valueSize)


class bdDEC(bdPrintStyle):
    "Supports decimal print style"

    def getString(self, value, useHex=False, skipTokens=False, valueSize=None):
        return bdPrintStyle.getString(self, value, useHex=useHex, skipTokens=skipTokens, valueSize=valueSize)


class bdBOTH(bdPrintStyle):
    "Supports both hex and decimal print style"

    def getString(self, value, useHex=False, skipTokens=False, valueSize=None):
        return bdPrintStyle.getString(self, value, useHex=False, skipTokens=skipTokens, valueSize=valueSize) + " " + \
               bdPrintStyle.getString(self, value, useHex=True, skipTokens=True, valueSize=valueSize)

    # Check the maximum string size that could be returned.
    # Overloading this because only want the decimal max size, not both.
    def maxStringSize(self):
        # Use a bdDEC style to figure out size.
        style = bdDEC(bits=self.bits, tokens=self.tokens)
        return style.maxStringSize()


class bdBOOL(bdPrintStyle):
    "Supports boolean print style"

    def isBool(self): return True

    def getString(self, value, useHex=False, skipTokens=False, valueSize=None):
        return bdPrintStyle.getString(self, value, useHex=useHex, valueSize=valueSize)


class bdSTR(bdPrintStyle):
    "Supports NSG string print style with each pair of characters reversed"

    def isString(self): return True

    def getString(self, value, useHex=False, skipTokens=False, valueSize=None):
        return bdPrintStyle.getString(self, value, skipTokens=False, useHex=useHex, valueSize=valueSize)


class bdSTRING(bdSTR):
    "Supports ordinary string print style"

    # Overloaded to change to non-NSG format.
    def extractValue(self, rawInteger, NSGstring=False):
        return bdSTR.extractValue(self, rawInteger=rawInteger, NSGstring=NSGstring)

    # Overloaded to change to non-NSG format.
    def makeRawInteger(self, value, NSGstring=False):
        return bdSTR.makeRawInteger(self, value=value, NSGstring=NSGstring)


class bdNONE(bdPrintStyle):
    "Supports unused print style (not displayed at all)"

    def isDisplayed(self): return False


class bdBCD(bdPrintStyle):
    "Prints a value as a binary coded decimal."

    # The default constructor is based on the FNV FW revision: 40 bits, aa.bb.cc.dddd
    # If you have a different size and format, inherit from bdBCD and overload this constructor.
    # The pattern uses a '%' character to mark digit locations. You can put anything else in it you want.
    def __init__(self, bits=40, signed=False, tokens=None, pattern="%%.%%.%%.%%%%"):
        bdPrintStyle.__init__(self, bits, signed, tokens)
        self.pattern = pattern

    # This requires a value to be passed, so is not implemented as __str__.
    # This is expected to be over-ridden when inherited to alter behavior.
    def getString(self, value, useHex=True, skipTokens=False, valueSize=0):
        "Convert value to a string."

        # Start with the leading white space.
        s = " " * (valueSize - len(self.pattern))

        digit = self.pattern.count('%')

        # Walk through the pattern replacing each "%" with a digit.
        for i in range(len(self.pattern)):
            character = self.pattern[i]
            if character == '%':
                digit -= 1
                character = "%x" % ((value >> (digit * 4)) & 0xF)
            s += character

        return s

    # Check the maximum string size that could be returned.
    def maxStringSize(self):
        return len(self.pattern)


# Descriptive strings to go with the derived styles above.
bdStyleStrings = {
    bdHEX   : "hex",
    bdDEC   : "decimal",
    bdBOTH  : "decimal & hex",
    bdSTR   : "string",
    bdSTRING: "string",
    bdBOOL  : "boolean"
}


# =========================================================================================================

def CHOP(a):
    a = a & 0xFFFFFFFF
    a = (a & 0xffff) + ((a >> 16) << 4) - (a >> 16);
    a = a & 0xFFFFFFFF
    return a;


def MOD28(a):
    a = CHOP(a);
    if (a >= BASE): a -= BASE;
    return a;


def MOD(a):
    a = CHOP(a);
    a = MOD28(a);
    return a;


## Helper function for Adler-32b checksums
ADLERINIT = 1  # Initial value required for adler32 algorithm
BASE = 65521  # largest prime smaller than 65536
NMAX = 5552  # NMAX is the largest n such that 255n(n+1)/2 + (n+1)(BASE-1) <= 2^32-1


def fwAdlerChecksum32(bytes, size=None, skip=0, adler=ADLERINIT):
    '''
    Calculates a Adler-32b checksum for an array of 'bytes'
    Default 'size' will be len(bytes)
    Use 'skip' to skip starting bytes (default 0)
    '''
    if size == None: size = len(bytes)

    idx = skip
    size -= skip
    len = size

    # split Adler-32 into component sums
    sum2 = (adler >> 16) & 0xffff;
    adler &= 0xffff;

    # do length NMAX blocks -- requires just one modulo operation
    while (len >= NMAX):
        len -= NMAX;
        n = NMAX / 16;  # NMAX is divisible by 16
        for n in range(0, NMAX / 16):
            for do16 in range(0, 16):
                adler += bytes[idx];
                adler &= 0xFFFFFFFF
                idx += 1;
                sum2 += adler;
                sum2 &= 0xFFFFFFFF
                len -= 1;

        adler = MOD(adler);
        sum2 = MOD(sum2);

    # do remaining bytes (less than NMAX, still just one modulo)
    if (len > 0):
        # avoid modulos if none remaining
        while (len >= 16):
            for do16 in range(0, 16):
                adler += bytes[idx];
                adler &= 0xFFFFFFFF
                idx += 1;
                sum2 += adler;
                sum2 &= 0xFFFFFFFF
                len -= 1;

        while (len > 0):
            adler += bytes[idx];
            adler &= 0xFFFFFFFF
            idx += 1;
            sum2 += adler;
            sum2 &= 0xFFFFFFFF
            len -= 1;

        adler = MOD(adler);
        sum2 = MOD(sum2);

    # return recombined sums
    adler = adler & 0xFFFFFFFF
    sum2 = sum2 & 0xFFFF
    sum2 = sum2 << 16

    return adler | sum2;


## Helper function for 32b checksum from FNV FW.
def fnvChecksum32(bytes, size=None, skip=0):
    '''
    FNV FW 32b checksum for an array of 'bytes'
    Default 'size' will be len(bytes)
    Use 'skip' to skip starting bytes (default 0)
    '''
    if size == None: size = len(bytes)

    csum = 0
    idx = skip

    while idx < size:
        csum = 0xFFFFFFFF & (csum + bytes[idx] * (1 << (8 * (idx % 4))))
        idx += 1

    return 0xFFFFFFFF & (~(csum) + 1)


## Helper function for 32b checksums
def fwChecksum32(bytes, size=None, skip=0):
    '''
    Calculates a 32b checksum for an array of 'bytes'
    Default 'size' will be len(bytes)
    Use 'skip' to skip starting bytes (default 0)
    '''
    if size == None: size = len(bytes)

    a = 1
    b = 0
    idx = skip
    size -= skip

    while (size > 0):
        if size > 5550:
            tempSize = 5550
        else:
            tempSize = size

        size -= tempSize
        a += (bytes[idx])
        idx += 1
        b += a
        tempSize -= 1

        while (tempSize > 0):
            a += (bytes[idx])
            idx += 1
            b += a
            tempSize -= 1

        a = (a & 0xffff) + (a >> 16) * 15
        b = (b & 0xffff) + (b >> 16) * 15

    if a >= 65521: a -= 65521
    b = (b & 0xffff) + (b >> 16) * 15
    return ((b << 16) | a)


## Helper function for 8b checksums
def fwChecksum8(bytes, size=None, skip=0):
    '''
    Calculates an 8b checksum for an array of 'bytes'
    Default 'size' will be len(bytes)
    Use 'skip' to skip starting bytes (default 0)
    '''
    if size == None: size = len(bytes)

    idx = skip
    sum = 0

    while idx < size:
        sum += bytes[idx]
        idx += 1

    sum = 256 - (sum & 0xFF)

    return sum


## Finds the length of the longest displayed name in a description list.
def longestName(description, floor=12):
    longest = floor
    if (description != None):
        for e in range(0, len(description), bdFIELDS):
            # Make an instance of the print style.
            style = description[e + bdSTYLE]()

            # Skip those we don't want to see.
            if style.isDisplayed() == True:
                l = len(description[e + bdNAME])
                if (longest < l): longest = l

    return longest


## Finds the length of the longest displayed value in a description list.
def longestValue(description, floor=8):
    longest = floor
    if (description != None):
        for e in range(0, len(description), bdFIELDS):
            # Make an instance of the print style.
            style = description[e + bdSTYLE](bits=description[e + bdSIZE], signed=description[e + bdSIGN], tokens=description[e + bdTOKEN])

            # Skip those we don't want to see.
            if style.isDisplayed() == True:
                l = style.maxStringSize()
                if (longest < l): longest = l

    return longest


def getDescription(desc_dict, key):
    "returns description"
    description = None
    if key in desc_dict:
        description = desc_dict[key]
    else:
        minorV = None
        for k in desc_dict:
            if key[0] in k:
                if k[1] > minorV:
                    minorV = k[1]  # get the latest minorVersion for that majorVersion
        if minorV != None:
            description = desc_dict[(key[0], minorV)]
            print("WARNING!!!! Version %d.%d not implemented, using %d.%d" % (key[0], key[1], key[0], minorV))
        else:
            description = desc_dict[(0, 0)]
            print("ERROR!!!! Version %d.%d not implemented" % (key[0], key[1]))
            raise KeyError
    return description


# The following several methods make doc strings for bufdict and buflist classes.

def stringsFromDescription(description, strings):
    "Loops a description and extracts relevant strings for a doc string."

    for i in range(0, len(description), bdFIELDS):
        if description[i + bdSTYLE] != bdNONE:
            f_name = description[i + bdNAME]
            f_size = description[i + bdSIZE]
            f_info = description[i + bdHELP]
            try:
                f_type = bdStyleStrings[description[i + bdSTYLE]]
            except KeyError:
                f_type = 'other'
            strings.append([f_name, str(f_size), str(f_type), f_info])


def buildDocString(strings, brief=None):
    "Builds a doc string of bufdict or buflist content in table form."

    if brief != None:
        doc = brief + "\n\n"
    else:
        doc = ""

    nameLen = sizeLen = typeLen = infoLen = 0
    for s in strings:
        nameLen = max(nameLen, len(s[0]))
        sizeLen = max(sizeLen, len(s[1]))
        typeLen = max(typeLen, len(s[2]))
        infoLen = max(infoLen, len(s[3]))

    sep = '+' + '{0}' * nameLen + '+' + '{0}' * sizeLen + '+' + '{0}' * typeLen + '+' + '{0}' * infoLen + '+\n'
    doc += sep.format('-')
    header = True

    for s in strings:
        doc += '|' + s[0] + ' ' * (nameLen - len(s[0])) + \
               '|' + s[1] + ' ' * (sizeLen - len(s[1])) + \
               '|' + s[2] + ' ' * (typeLen - len(s[2])) + \
               '|' + s[3] + ' ' * (infoLen - len(s[3])) + \
               '|\n'

        if (header):
            doc += sep.format('=')
            header = False
        else:
            doc += sep.format('-')

    return doc


def generate_doc(description, brief=None):
    """
    Generates a string with a table containing fields names and types
    from a list of [name,type], e.g.:
    +---------------+------------+-------+---------------+
    | Name          | Size (bit) | Type  | Info          |
    +===============+============+=======+===============+
    |partition      |8           |hex    |partition      |
    +---------------+------------+-------+---------------+
    |type           |1           |boolean|type           |
    +---------------+------------+-------+---------------+
    |option         |1           |boolean|option         |
    +---------------+------------+-------+---------------+
    |offset         |32          |hex    |offset         |
    +---------------+------------+-------+---------------+

    :param description: bufdict description
    :return string: ascii table based on input
    """
    strings = []
    strings.append([" Name ", " Size ", " Type ", " Info "])
    stringsFromDescription(description, strings)
    return buildDocString(strings, brief)


def generate_buflist_doc(header, entry, tail=None, brief=None):
    """
    Generates a string with a table containing fields names and types
    from a list of [name,type], e.g.:
    +--------+------------+-------+-----------------------------------------+
    | HEADER | Size (bit) | Type  | Info                                    |
    +========+============+=======+=========================================+
    |version |16          |decimal|Major Version Number                     |
    +--------+------------+-------+-----------------------------------------+
    |minorVer|16          |decimal|Minor Version Number                     |
    +--------+------------+-------+-----------------------------------------+
    |start   |32          |other  |First register address                   |
    +--------+------------+-------+-----------------------------------------+
    |size    |32          |decimal|Number of consecutive addresses to access|
    +--------+------------+-------+-----------------------------------------+
    | ENTRY  | ---------  | ----  | ----                                    |
    +--------+------------+-------+-----------------------------------------+
    |value   |32          |hex    |CSR content                              |
    +--------+------------+-------+-----------------------------------------+

    :param HEADER: bufdict description of the header
    :param ENTRY: bufdict description of each entry
    :param TAIL: bufdict description of the tail (optional)
    :return string: ascii table based on input
    """
    strings = []
    strings.append([" Name ", " Size ", " Type ", " Info "])
    strings.append([" HEADER ", "------", "----", "----"])
    stringsFromDescription(header, strings)

    strings.append([" ENTRIES ", "------", "----", "----"])
    stringsFromDescription(entry, strings)

    if tail != None:
        strings.append([" TAIL ", "------", "----", "----"])
        stringsFromDescription(tail, strings)

    return buildDocString(strings, brief)


class bufdict(object):
    """
    Base class for buffer structures.

    description - List that defines all the allowed contents.
    name        - Alternate name for the object. Default will be the class name.
    version     - Version number to compare against. -1 means 'no version checking'.
    namesize    - Number of characters to use when printing field names. None means auto-size.
    valuesize   - Number of characters to use when printing field values. None means auto-size.
    filename    - File to load during object creation.
    buf         - Buffer to load from during object creation.
    offset      - Offset (in bits) into the buffer from which to load. Meaningless if no buffer specified.
    other       - Another object to copy from during object creation. Copy Constructor.
    raw         - Set to True to force raw hex string as the print style. Seldom used.

    Child classes should (almost) always provide a 'description' at minimum to solidify the content.
    The 'name' parameter is not expected to be used. The child class name should be descriptive enough.
    'namesize' and 'valuesize' will be auto-sized if not specified.

    'filename', 'buf', 'offset' and 'other' give the user ways to fill content during construction.
    As such, all child classes are expected to pass 'filename', 'buf', 'offset' and 'other' to the user.
    The default should remain None for all these, but don't leave them out. They're useful!
    """

    def __init__(self, description=None, version=-1, name=None, namesize=None, valuesize=None,
                 filename=None, buf=None, offset=0, other=None, raw=False):
        self.version = version
        self.info = description
        self.bytes = 0
        self.entry = {}  # The actual values for each key.
        self.keyorder = {}  # Facilitates quick info look-up.
        self._index_ = 0  # For iterator support.
        self.itertype = 0  # Supporting multiple iterators.
        self.K_TYPE = 0  # Iterate over keys (default).
        self.V_TYPE = 1  # Iterate over values.
        self.KV_TYPE = 2  # Iterate over key/value pairs.
        self.raw = raw  # Support raw __str__() when desired.

        if name != None:
            self.__name__ = name
        else:
            self.__name__ = self.__class__.__name__  # pull the class name up higher for convenience.

        if namesize == None:
            self.namesize = longestName(description)
        else:
            self.namesize = namesize

        if valuesize == None:
            self.valuesize = longestValue(description)
        else:
            self.valuesize = valuesize

        # Track the size of the help strings.
        self._help_size_ = 0
        for e in range(0, len(self.info), bdFIELDS):
            if len(self.info[e + bdHELP]) > self._help_size_:
                self._help_size_ = len(self.info[e + bdHELP])

        if (self.info != None):  # An empty bufdict is valid.
            bits = 0  # Will count the bits used...

            # Create each key now. No other keys are allowed.
            for e in range(0, len(self.info), bdFIELDS):
                bits += self.info[e + bdSIZE]  # Counting up the bits used.
                key = self.info[e]  # Get a key from the description list.
                self.keyorder[key] = e  # Remember the key order for later.
                value = self.info[e + bdINIT]  # Initial (default) Value.
                tokens = self.info[e + bdTOKEN]  # Tokens for this key.
                if tokens != None and tokens.has_key(value):
                    value = tokens[value]  # Token string converted to actual value.
                self.entry[key] = value  # Internal storage of the value.

            self.bytes = int(math.ceil(bits / 8))  # Bytes used by the entire structure.

            if (filename != None): self.fromfile(filename)
            if (buf != None): self.frombuf(buf=buf, offset=offset)
            if (other != None): self.copy(other)

        # Keep this at the end of init!
        # This stops further attribute creation. The object is locked.
        self.__initialised = True

    def help(self, key=None, output=sys.__stdout__, full=False):
        "Shows help info for the data members"
        print >> output, self.helpstring(key=key, full=full)

    def set(self):
        "Set contents all at once"
        # The derived class must implement this
        pass

    def has_key(self, key):
        "Ask if this object contains a particular key (or attribute)."
        return self.__contains__(key)

    def __contains__(self, key):
        "has_key(key) -> True if key exists, else False"
        return key in self.entry

    def keys(self):
        "keys() -> Ordered list of keys"
        keylist = []
        for e in range(0, len(self.info), bdFIELDS):
            # Make an instance of the print style.
            style = self.info[e + bdSTYLE]()

            # Skip those we don't want to see.
            if style.isDisplayed() == True:
                keylist.append(self.info[e])

        return keylist

    def items(self):
        "List of (key, value) pairs, as 2-tuples"
        itemlist = []
        for e in range(0, len(self.info), bdFIELDS):
            # Make an instance of the print style.
            style = self.info[e + bdSTYLE]()

            # Skip those we don't want to see.
            if style.isDisplayed() == True:
                k = self.info[e]
                itemlist.append((k, self[k]))
        return itemlist

    def values(self):
        "List of values"
        values = []
        for e in range(0, len(self.info), bdFIELDS):
            values.append(self[self.info[e]])
        return values

    # These also make sense for a bufdict object since there's more stuff.
    def bitsize(self, key=None):
        "Total bits or the bit size of a particular entry"
        if key == None:
            bits = 0
            for e in range(0, len(self.info), bdFIELDS):
                bits += self.info[e + bdSIZE]
            return bits

        elif not self.entry.has_key(key):
            print("Invalid key:", key)
            raise KeyError

        return self.info[self.keyorder[key] + bdSIZE]

    def bitsizes(self):
        "List of bit field sizes of all members"
        values = []
        for e in range(0, len(self.info), bdFIELDS):
            values.append(self.info[e + bdSIZE])
        return values

    def byte_size(self):
        return bufdict.bytesize(self)

    def bytesize(self):
        "Bytes taken in a buffer by the entire object"
        return int(math.ceil(bufdict.bitsize(self) / 8.0))

    def bitposition(self, key):
        "Finds the bit position of a particular entry"
        if not self.entry.has_key(key):
            print("Invalid key:", key)
            raise KeyError
            return -1
        location = 0
        for e in range(0, len(self.info), bdFIELDS):
            if key == self.info[e]:
                return location
            location += self.info[e + bdSIZE]

    def bitpositions(self):
        "List of bit positions of all members"
        values = []
        location = 0
        for e in range(0, len(self.info), bdFIELDS):
            values.append(location)
            location += self.info[e + bdSIZE]
        return values

    def default(self, key):
        "Default value for a particular entry"
        if not self.entry.has_key(key):
            print("Invalid key:", key)
            raise KeyError
            return -1
        return self.info[self.keyorder[key] + bdINIT]

    def defaults(self):
        "List of default values of all members"
        values = []
        for e in range(0, len(self.info), bdFIELDS):
            values.append(self.info[e + bdINIT])
        return values

    def helpstring(self, key=None, full=False):
        "Returns a help string for the data members."
        format_string = "%" + str(self.namesize) + "s - %s\n"
        if key == None or not self.entry.has_key(key):
            helpstring = "%s contains the following:\n" % (self.__name__)
            for e in range(0, len(self.info), bdFIELDS):
                if (full == False):
                    # Make an instance of the print style.
                    style = self.info[e + bdSTYLE]()

                    # Skip those we don't want to see.
                    if style.isDisplayed() == False: continue

                helpstring += format_string % (self.info[e], self.info[e + bdHELP])
            return helpstring
        return self.info[self.keyorder[key] + bdHELP]

    def describe(self, header=True):
        "Returns a string in readable format of the description list."

        formatstring = "%%%ds %%4s %%6s %%10s %%10s %%6s %%s\n" % self.namesize

        if header == True:
            mystring = formatstring % ('NAME', 'SIZE', 'SIGNED', 'DEFAULT', 'STYLE', 'TOKENS', 'Description')
        else:
            mystring = ''

        for e in range(0, len(self.info), bdFIELDS):
            mystring += formatstring % (self.info[e + bdNAME],
                                        str(self.info[e + bdSIZE]),
                                        str(self.info[e + bdSIGN]),
                                        str(self.info[e + bdINIT]),
                                        self.info[e + bdSTYLE].__name__,
                                        str(self.info[e + bdTOKEN] != None),
                                        str(self.info[e + bdHELP]))
        print(mystring)

    def iteritems(self):
        "Iterate (key, value) pairs"
        self.__setattr__('itertype', self.KV_TYPE, True)
        self.__setattr__('_index_', 0, True)
        return self

    def iterkeys(self):
        "Iterate keys"
        self.__setattr__('itertype', self.K_TYPE, True)
        self.__setattr__('_index_', 0, True)
        return self

    def itervalues(self):
        "Iterate values"
        self.__setattr__('itertype', self.V_TYPE, True)
        self.__setattr__('_index_', 0, True)
        return self

    def __iter__(self):
        "This catches the default iterator."
        if self._index_ != 0:
            self.__setattr__('itertype', self.K_TYPE, True)
            self.__setattr__('_index_', 0, True)
        return self

    def next(self):
        if (self._index_ == len(self.entry)):
            raise StopIteration
        i = self._index_ * bdFIELDS
        key = self.info[i]
        self.__setattr__('_index_', self._index_ + 1, True)

        if self.itertype == self.K_TYPE: return key
        if self.itertype == self.V_TYPE: return self.entry[key]
        if self.itertype == self.KV_TYPE: return key, self.entry[key]
        raise NotImplementedError  # Unrecognized iterator type. Code bug.

    def item_string(self, key, valueSize=0):
        "Return the string of a particular item in proper style with tokenization."
        e = self.keyorder[key]
        style = self.info[e + bdSTYLE](bits=self.info[e + bdSIZE], tokens=self.info[e + bdTOKEN])
        value = self[key]
        return style.getString(value, valueSize=valueSize)

    def tokens(self, key):
        "Return the full token dictionary for a particular key."
        if (not self.entry.has_key(key)):
            print("Invalid key:", key)
            raise KeyError
        return self.info[self.keyorder[key] + bdTOKEN]

    def token(self, key):
        "Return the token string for a value or None if no token exists."
        if (not self.entry.has_key(key)):
            print("Invalid key:", key)
            raise KeyError
        tokens = self.tokens(key)
        if tokens != None:
            value = self[key]
            for t in tokens:
                if tokens[t] == value:
                    return t
        return None

    def detoken(self, key, value):
        "Detokenize a value (change a token string to a number)."
        if (not self.entry.has_key(key)):
            print("Invalid key:", key)
            raise KeyError
        e = self.keyorder[key]
        style = self.info[e + bdSTYLE](tokens=self.info[e + bdTOKEN])
        return style.detoken(value)

    # Dictionary access to raw value.
    def __getitem__(self, key):
        "Get data by key name."
        # Is the key valid? Must already exist.
        if (not self.entry.has_key(key)):
            print("Invalid Key: ", key)
            raise KeyError

        style = self.info[self.keyorder[key] + bdSTYLE]()
        if style.isBool() == True:
            return (self.entry[key] != 0)
        else:
            return self.entry[key]

    # Dictionary access to set the value (can be tokenized value or in string form)
    def __setitem__(self, key, value):
        "Set data by key string."
        if not self.entry.has_key(key):
            print("Invalid Key: ", key)
            raise KeyError

        e = self.keyorder[key]
        size = self.info[e + bdSIZE]
        style = self.info[e + bdSTYLE](bits=size, tokens=self.info[e + bdTOKEN])
        self.entry[key] = style.detoken(value)

        # If the user changes a calculated field, we may need special handling.
        if size == 0:
            calculate = self._magic_fields()
        else:
            calculate = True

        if calculate: self._calculated_fields()

    # Attribute access (dot syntax)
    def __setattr__(self, item, value, force=False):
        "Set data by attribute string."
        # This allows normal attributes to be set in __init__()
        # After init, the object contents are locked.
        if (force and self.__dict__.has_key(item)) or \
                not self.__dict__.has_key('_bufdict__initialised') or \
                item == 'raw':
            self.__dict__[item] = value
        else:
            self.__setitem__(item, value)

    # Attribute access (dot syntax)
    def __getattr__(self, item):
        "Get data by attribute string."
        if self.entry.has_key(item): return self.__getitem__(item)
        if self.__dict__.has_key(item): return self.__dict__[item]
        raise KeyError

    def __delattr__(self, item):
        "Throws an exception. Bufdict objects have rigidly defined contents."
        raise Exception("Cannot delete attributes from a bufdict")

    def __len__(self):
        """
        Number of attributes in the object.
        Careful! This counts hidden members as well (bdNONE).
        """
        return len(self.entry)

    def __eq__(self, other, keylist=None):
        "Compares the guts to another instance with option of key list"
        if type(other) is type(self):
            if keylist == None:
                return (self.entry == other.entry)
            else:
                for key in keylist:
                    if self.entry[key] != other.entry[key]: return False
                return True
        else:
            return False

    def __ne__(self, other):
        "Compares the guts to another instance."
        return not self.__eq__(other)

    def __repr__(self):
        return str(self)

    def __str__(self, header=True, delimiter='\n', raw=None, show_names=True, show_help=False,
                sort=False, hex_dump=False, hex_transition_size=64):
        """
        Default string creation used mainly for printing.

        You can override this in your derived class to change the default values
        of the parameters for simple customization. For example, an fconfig
        class will probably show the help strings by default but most NLBA
        objects do not show help. Or maybe you want them tab-delimited on
        one line instead of one value per line...

        Of course, you may also fully override this method and create a fully
        customized method of string creation. I typically do this for logs
        to make them very readable since there will be many at once.
        """

        if (self.bytes == 0): return ''

        nameformat = "%%%ds " % self.namesize
        valueformat = "%%%ds" % self.valuesize
        helpformat = "  %%%ds : " % self._help_size_

        # Get the keys first
        mykeys = self.keys()
        if sort == True: mykeys.sort()

        mystring = ''

        if header: mystring += self.__name__ + ':' + delimiter

        for key in mykeys:
            e = self.keyorder[key]
            value = self[key]

            # Do everything in hex? (including bdNONE!)
            if (hex_dump):
                style = bdHEX(hexDump=True, hexTransitionSize=hex_transition_size)
            else:
                style = self.info[e + bdSTYLE](bits=self.info[e + bdSIZE], tokens=self.info[e + bdTOKEN])

            # Skip those we don't want to see (bdNONE print style)
            if style.isDisplayed() == False: continue

            # Do we want help strings at the same time?
            if show_help != False:
                mystring += helpformat % self.info[e + bdHELP]

            if show_names == True:
                mystring += nameformat % key

            # Get the string version of the value.
            s = style.getString(value, valueSize=self.valuesize)

            if self.info[e + bdSTYLE] == bdHEX:
                bits = float(self.info[e + bdSIZE])
                if (False == hex_dump) and bits <= hex_transition_size:
                    mystring += s
                else:
                    # Tack on a space if the MSB is just a nibble.
                    digits = len(s)
                    if 0 != (digits % 2):
                        s = ' ' + s
                        digits += 1

                    # Parse up the string in hex dump format.
                    bytes = 0
                    while digits > 0:
                        if bytes == 16:
                            bytes = 0
                            mystring += '\n ' + ' ' * self.namesize

                        bytes += 1
                        this_byte = s[0:2]
                        s = s[2:]
                        digits -= 2

                        mystring += ' ' + this_byte

                    mystring += '\n'
            else:
                mystring += s

            mystring += delimiter

        return mystring

    def _calculated_fields(self):
        """
        The derived class must implement this for the specific details.

        This is used for attributes which require some calculation based on other
        contents of other values. This can also be used to add your own data
        members that are not in the raw buffer data passed to and from the drive.

        MRR log entries, for example, have a calculated attribute for the run time
        in microseconds, which is calculated from the start and end time
        values that come from the drive in the real MRR log.

        Calculated, additional fields are entered into the description list with
        a bit size of 0 so that they are not parsed or included in any buffer
        transfers of data. But, of course, you must override this method to
        do the calculations for all such fields.
        """
        pass

    def _magic_fields(self):
        """
        The derived class must implement this for the specific details.
        This is called when the user sets a magic field that causes action elsewhere.
        For example, perhaps you have a data member whose data, when set, must be
        translated into content in the real fields.

        Return True to have __setitem__() call _calculated_fields() afterward.
        Return False to have __setitem__() skip _calculated_fields().
        """
        return True

    def copy(self, other):
        "Copies contents from an 'other' object."
        if type(other) != type(self):
            raise Exception("Wrong entry type")
        for e in range(0, len(self.info), bdFIELDS):
            if self.info[e + bdSIZE] <= 0: continue
            key = self.info[e]
            self.entry[key] = other[key]
        self._calculated_fields()

    def makeGiantInteger(self, buf, offset=0):
        "Make a giant integer from a byte buffer. Helper method used by from_buf()."

        if offset == None: offset = 0
        bytesize = bufdict.bytesize(self)
        if bytesize == 0: return offset

        # Read the whole entry into a giant integer...
        # Deal with starting location in the middle of a byte first.
        offset = int(offset)  # Make sure it's an integer.
        byte = offset >> 3  # First byte in which data appears.
        location = offset % 8  # Number of bits to skip in the first byte.
        if location > 0:
            bitsdone = 8 - location  # Number of bits we're getting from the first byte.
            giant_integer = long((buf[byte] & (256 - (1 << location))) >> location)
            byte += 1
        else:
            giant_integer = long(0)
            bitsdone = 0

        # Get the rest of the bits needed, rounding up to nearest byte.
        bitsize = bufdict.bitsize(self)
        while bitsdone < bitsize:
            giant_integer = giant_integer | (buf[byte] << bitsdone)
            bitsdone += 8
            byte += 1

        return giant_integer

    def fromGiantInteger(self, giant_integer):
        "Get content from a giant integer. Helper method used by from_buf()."

        # Parse the log entry.
        for e in range(0, len(self.info), bdFIELDS):
            bits = self.info[e + bdSIZE]

            # Skip calculated fields
            if bits <= 0: continue

            # Make an instance of the print style.
            signed = self.info[e + bdSIGN] != 0
            style = self.info[e + bdSTYLE](bits=bits, signed=signed)

            # Extract the raw integer for this data member.
            mask = (1 << bits) - 1
            rawInteger = giant_integer & mask
            giant_integer = giant_integer >> bits

            # Get the correct value from the raw integer.
            value = style.extractValue(rawInteger)
            self.entry[self.info[e]] = value

            if self.version >= 0 and self.info[e] == 'version' and self.version != value:
                raise Exception(("%s Version Mismatch: expect 0x%04X, actual 0x%04X" % (self.__name__, self.version, value)))

        self._calculated_fields()

    def from_buf(self, buf, offset=0):
        return self.frombuf(buf=buf, offset=offset)

    def frombuf(self, buf, offset=0):
        "Get content from a binary buffer"
        if offset == None: offset = 0
        giant_integer = self.makeGiantInteger(buf=buf, offset=offset)
        self.fromGiantInteger(giant_integer)
        return offset + self.bitsize()

    def to_buf(self, buf=None, offset=0):
        return self.tobuf(buf=buf, offset=offset)

    def tobuf(self, buf=None, offset=0):
        """
        Send content to a binary buffer.
        If buf==None, a buf is created and returned.
        If offset!=None, new offset is returned.
        """

        if offset == None: offset = 0
        bytesize = bufdict.bytesize(self)
        bitsize = bufdict.bitsize(self)

        if buf == None:
            buf = bytearray(bytesize)
            offset = 0
            returnbuf = True
        else:
            returnbuf = False

        if bytesize == 0:
            if returnbuf:
                return buf
            else:
                return offset

        # Crunch into a giant integer first.
        giant_integer = 0
        for f in range(0, len(self.info), bdFIELDS):
            e = len(self.info) - f - bdFIELDS
            if (self.info[e + bdSIZE] <= 0): continue

            bits = self.info[e + bdSIZE]
            if bits <= 0: continue

            # Make an instance of the print style.
            style = self.info[e + bdSTYLE](bits=bits)

            giant_integer = giant_integer << bits
            giant_integer += style.makeRawInteger(value=self.entry[self.info[e]])

        # Send the giant integer to the buffer...
        # Deal with starting location in the middle of a byte first.
        offset = int(offset)  # Make sure it's an integer.
        byte = offset >> 3  # First byte in which data will reside.
        location = offset % 8  # Number of bits to skip in the first byte.
        if location > 0:
            bitsdone = 8 - location  # Number of bits we're filling in the first byte.
            buf[byte] &= ((1 << location) - 1)  # Clear out the bits we're going to fill.
            buf[byte] |= (giant_integer & ((1 << (bitsdone)) - 1)) << location  # Fill the bits.
            giant_integer = giant_integer >> bitsdone  # Discard the bits we just used.
            byte += 1
        else:
            bitsdone = 0

        # The rest of the bytes get stomped directly.
        while bitsdone < bitsize:
            buf[byte] = giant_integer & 0xFF
            giant_integer = giant_integer >> 8
            bitsdone += 8
            byte += 1

        if returnbuf:
            return buf
        else:
            return offset + bitsize

    def from_file(self, filename=None, file=None):
        return self.fromfile(filename=filename, file=file)

    def fromfile(self, filename=None, file=None):
        "Get content from a binary file"
        if (filename != None): file = open(filename, 'rb')
        raw_data = file.read(self.bytesize())
        buf = [ord(x) for x in raw_data]
        self.frombuf(buf=buf)
        if (filename != None): file.close()

    def to_file(self, filename=None, file=None, append=False, offset=0):
        "Send content to a binary file"
        return self.tofile(filename=filename, file=file, append=append, offset=offset)

    def tofile(self, filename=None, file=None, append=False, offset=0):
        "Send content to a binary file"
        if (filename != None):
            if (append):
                file = open(filename, 'wb+')
            else:
                file = open(filename, 'wb')

        faux_buf = bytearray(self.bytesize() + offset)
        self.tobuf(buf=faux_buf, offset=offset)
        s = "".join([chr(x) for x in faux_buf])
        file.write(s)
        if (filename != None): file.close()

    def txt_to_file(self, filename=None, file=None, append=False):
        "Send content to a human-readable text file"
        return self.txttofile(filename=filename, file=file, append=append)

    def txttofile(self, filename=None, file=None, append=False):
        "Send content to a human-readable text file"
        if (filename != None):
            if (append):
                file = open(filename, 'a')
            else:
                file = open(filename, 'w')
        print >> file, self.__str__()
        if (filename != None): file.close()


class bufarray(bytearray, bufdict):
    """
    Adds bufdict behavior to a bytearray. Behaves primarily like a bytearray.

    A bufarray inherits directly from a bufdict and python bytearray, so it's quite
    literally a combination of both. You will make a bufarray in exactly the same
    way described for bufdict. The basic use case is when the buffer interaciton
    with the device has a structured header (the bufdict part) followed by a
    bytearray. Then in twidl you will manipulate the object exactly the same as
    you would a bytearray.

    The only thing you really need to know is that you should specify a size for the
    bytearray during construction. The first parameter to the constructor is the
    size of the bytearray.

    size        - The size, in bytes, of the bytearray.
    description - List that defines all the allowed contents.
    name        - Alternate name for the object. Default will be the class name.
    version     - Version number to compare against. -1 means 'no version checking'.
    namesize    - Number of characters to use when printing field names. None means auto-size.
    valuesize   - Number of characters to use when printing field values. None means auto-size.
    filename    - File to load during object creation.
    buf         - Buffer to load from during object creation.
    offset      - Bit offset into the buffer from which to load.
    other       - Another object to copy from during object creation. Copy Constructor.
    raw         - Set to True to force raw hex string as the print style. Seldom used.

    """

    def __init__(self, size=None, description=None, version=-1, name=None, namesize=None,
                 valuesize=None, filename=None, buf=None, offset=0, other=None, raw=False):

        # Make the bytearray first.
        bytearray.__init__(self, size)
        self.xor_result = False

        # Then make the bufdict.
        bufdict.__init__(self, description=description, version=version, name=name,
                         namesize=namesize, valuesize=valuesize, filename=filename,
                         buf=buf, offset=offset, other=other, raw=raw)

    def __setslice__(self, i, j, other):
        # Copy data from other directly using memory view.
        # This avoids calls to _calculated_fields on each byte copied.
        buf = memoryview(self)
        buf[i:j] = other[:j - i]
        # Now call _calculated_fields only once after the full copy is done.
        self._calculated_fields()

    def __getitem__(self, key):
        # Optimized for bytearray access.
        # If that fails, then try the bufdict pieces.
        try:
            return bytearray.__getitem__(self, key)
        except:
            return bufdict.__getitem__(self, key)

    def __setitem__(self, key, value):
        # Optimized for bytearray access.
        # If that fails, then try the bufdict pieces.
        try:
            bytearray.__setitem__(self, key, value)
            self._calculated_fields()
        except:
            bufdict.__setitem__(self, key, value)

    def __repr__(self):
        return str(self)

    def __str__(self, header=True, delimiter='\n', raw=None, show_names=True, show_help=False,
                sort=False, hex_dump=False, hex_transition_size=64,
                big_endian=False, values_per_line=16, bytes_per_value=1):

        myString = bufdict.__str__(self, header=header, delimiter=delimiter, raw=raw, show_names=show_names,
                                   show_help=show_help, sort=sort, hex_dump=hex_dump, hex_transition_size=hex_transition_size)

        if bytes_per_value != 1 and bytes_per_value != 2 and bytes_per_value != 4 and bytes_per_value != 8:
            raise Exception('A hex dump must be 1, 2, 4, or 8 bytes at a time, not ' + str(bytes_per_value))

        if delimiter != '\n': myString += '\n'
        if header:
            if bytes_per_value <= 1:  myString += 'bytearray:'
            if big_endian:
                myString += 'Big endian bytearray:'
            else:
                myString += 'Little endian bytearray:'

        format_string = ' %%0%dX' % (2 * bytes_per_value)
        for i in range(0, bytearray.__len__(self), bytes_per_value):
            if ((i % values_per_line) == 0): myString += "\n"

            tmpData = 0
            for j in range(bytes_per_value):
                if big_endian:
                    tmpData = (tmpData << 8) + bytearray.__getitem__(self, i + j)
                else:
                    tmpData = (tmpData << 8) + bytearray.__getitem__(self, i + bytes_per_value - j - 1)

            if self.xor_result:
                myString += (format_string % tmpData).replace('0', '.')
            else:
                myString += (format_string % tmpData)

        return myString

    def bitsize(self, key=None):
        "Total bits or the bit size of a particular entry"
        if key is None:
            return bufdict.bitsize(self) + 8 * bytearray.__len__(self)
        elif (isinstance(key, int)) and (key >= 0) and (key < bytearray.__len__(self)):
            return 8
        else:
            return bufdict.bitsize(self, key)

    def byte_size(self):
        return bufarray.bytesize(self)

    def bytesize(self):
        "Bytes taken in a buffer by the entire object"
        return int(math.ceil(bufarray.bitsize(self) / 8.0))

    def to_buf(self, buf=None, offset=0):
        return bufarray.tobuf(self, buf, offset)

    def tobuf(self, buf=None, offset=0):
        bytesize = bufarray.bytesize(self)
        bitsize = bufarray.bitsize(self)

        if buf == None:
            buf = bytearray(bytesize)
            offset = 0
            returnbuf = True
        else:
            returnbuf = False

        bufdict.tobuf(self, buf=buf, offset=offset)
        byte = bufdict.bytesize(self)
        for i in range(bytearray.__len__(self)):
            buf[byte] = bytearray.__getitem__(self, i)
            byte += 1

        if returnbuf:
            return buf
        else:
            return offset + bitsize

    def from_buf(self, buf, offset=0):
        return bufarray.frombuf(self, buf, offset)

    def frombuf(self, buf, offset=0):
        "Get content from a binary buffer"
        bufdict.frombuf(self, buf=buf, offset=offset)
        byte = bufdict.bytesize(self)
        for i in range(bytearray.__len__(self)):
            bytearray.__setitem__(self, i, buf[byte])
            byte += 1

        # Call calculated fields in case they depend on the byte array content.
        self._calculated_fields()
        return offset + self.bitsize()

    def copy(self, other):
        "Copies contents from an 'other' object."
        self[:] = other[:]
        bufdict.copy(self, other)

    def __eq__(self, other, keylist=None):
        "Compares the guts to another instance with option of key list."
        if not bufdict.__eq__(self, other, keylist): return False
        return self[:] == other[:]

    def __ixor__(self, other):
        "self ^= other, other is another bufarray or an integer."
        if isinstance(other, int):
            for i in range(bytearray.__len__(self)): self[i] ^= other
        else:
            size = min(bytearray.__len__(self), bytearray.__len__(other))
            for i in range(size): self[i] ^= other[i]
        self.__setattr__('xor_result', True, force=True)
        return self

    def __xor__(self, other):
        "result = self ^ other, other is another bufarray or an integer."
        result = self.__class__(other=self)  # Make a copy of myself to return
        result.__ixor__(other)
        return result

    def weight(self):
        "Returns the weight of the array (the total number of ones in the data)."
        weight = 0
        for i in range(bytearray.__len__(self)):
            n = self[i]

            while n != 0:
                weight += 1
                n &= n - 1

        return weight


def colname_value_tuple_list(args):
    pass


class buflist(object):
    """
    Base class for a list of bufdict objects.

    entryclass   - Bufdict child class to hold each entry in the list.
    headerclass  - Bufdict child class to hold the header info prior to entries.
    tailclass    - Bufdict child class to hold tail data after the list (if any).
    name         - Alternate name for the object. Default will be the class name.
    filename     - File to load during object creation.
    buf          - Byte buffer to load from during object creation.
    other        - Another object to copy from during object creation. Copy Constructor.
    raw          - Set to True to force raw hex string as the print style. Seldom used.
    strict       - Set to False to disable strict entry type checking.
    checksum32   - Alternative function to calculate 32b checksums on the fly.
    majorVersion - Major version number to compare against.
    minorVersion - Minor version number to compare against.

    Buflist child classes MUST provide an 'entryclass' and 'headerclass'.
    The header MUST have a 'size' entry at minimum, even if it's a calculated field.
    The 'size' in the header is the number of entries in the list.

    'filename', 'buf' and 'other' can provide content during object construction.
    All child classes are expected to make 'filename', 'buf', 'offset' and 'other'
    available to the user. Default should remain None but don't leave them out!
    """

    def __init__(self, entryclass, headerclass, tailclass=None, name=None, filename=None, buf=None, other=None,
                 raw=False, strict=True, checksum32=fwChecksum32, majorVersion=None, minorVersion=None):

        # Special syntax for these to get them created first.
        # These are needed by the derived __setattr__ method, so they
        # create a catch 22 if accessed with normal "dot" syntax.
        # For example, we cannot do this:
        #   self.headerclass = headerclass
        # Instead, we avoid a call to self.__setattr__ like this:
        object.__setattr__(self, 'headerclass', headerclass)
        object.__setattr__(self, 'tailclass', tailclass)
        object.__setattr__(self, 'dummyentry', entryclass(majorVersion=majorVersion, minorVersion=minorVersion))
        object.__setattr__(self, 'entryclass', entryclass)
        object.__setattr__(self, 'name', name)
        object.__setattr__(self, '_index_', 0)
        object.__setattr__(self, 'raw', raw)
        object.__setattr__(self, 'strict', strict)
        object.__setattr__(self, 'checksum32', checksum32)
        object.__setattr__(self, 'majorVersion', majorVersion)
        object.__setattr__(self, 'minorVersion', minorVersion)

        if name != None:
            object.__setattr__(self, '__name__', name)
        else:
            object.__setattr__(self, '__name__', self.__class__.__name__)  # pull the class name up higher for convenience.

        # Make the header and tail objects.
        # if majorVersion != None:
        object.__setattr__(self, 'header', headerclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion))
        object.__setattr__(self, 'entryClass', entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion))
        if (tailclass != None):
            object.__setattr__(self, 'tail', tailclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion))
        else:
            object.__setattr__(self, 'tail', None)

        # Clear out the internal list and then fill it if we can.
        object.__setattr__(self, 'buflist', [])
        if (filename != None): self.fromfile(filename=filename)
        if (buf != None): self.frombuf(buf=buf)
        if (other != None): self.copy(other)

    def help(self, output=sys.__stdout__):
        "Shows help strings for the data members"
        print >> output, self.__name__, "contains one (", self.header.__name__, ") and a list of (", self.dummyentry.__name__, ") objects.\n"
        self.header.help()
        self.dummyentry.help()
        if self.tail != None: self.tail.help()

    def keys(self):
        return self.dummyentry.keys()

    def __contains__(self, key):
        return self.dummyentry.__contains__(key)

    def __len__(self):
        return len(self.buflist)

    def sort(self, key, reverse=False):
        "Sort by 'key'"
        if not self.dummyentry.has_key(key): raise KeyError
        sorted_list = sorted(self.buflist, key=operator.itemgetter(key), reverse=reverse)
        self.buflist = sorted_list

    # Attribute access (dot syntax)
    def __getattr__(self, item):
        # We must use this odd syntax to avoid recursion.
        if self.__dict__['header'].has_key(item): return self.__dict__['header'][item]
        if self.tail != None and self.tail.has_key(item): return self.__dict__['tail'][item]
        if self.__dict__.has_key(item): return self.__dict__[item]
        raise KeyError

    def __setattr__(self, k, v):
        # We must use this odd syntax to avoid recursion.
        if self.__dict__['header'].has_key(k):
            self.__dict__['header'][k] = v
        elif self.tail != None and self.tail.has_key(k):
            self.__dict__['tail'][k] = v
        elif self.__dict__.has_key(k):
            self.__dict__[k] = v
        else:
            raise KeyError

    def __getitem__(self, key):
        if type(key) is slice:
            return self.__getslice__(key.start, key.stop, key.step)
        else:
            return self.buflist[key]

    def __setitem__(self, k, v):
        copy = self.entryclass(other=v, majorVersion=self.majorVersion, minorVersion=self.minorVersion)
        self.buflist[k] = copy

    def __delitem__(self, key):
        del self.buflist[key]
        self.header['size'] = len(self)

    def __getslice__(self, start, stop, step=1):
        copy = type(self)()  # Make a new buflist to return.

        if step > 0:  # Upward slice.
            if start == None: start = 0
            if stop == None or stop > len(self.buflist): stop = len(self.buflist)
            while start < stop:
                copy.append(self.buflist[start])
                start += step

        else:  # Backwards slice
            if stop == None: stop = -1
            if start == None or start > len(self.buflist) - 1: start = len(self.buflist) - 1
            while start > stop:
                copy.append(self.buflist[start])
                start += step

        return copy

    def __delslice__(self, i, j):
        while j > i:
            j -= 1
            del self[j]

    def __setslice__(self, i, j, other=None):
        # Enable buflist[i:j] = None
        if other == None:
            return self.__delslice__(i, j)

        # Enable buflist[i:j] = []
        if type(other) == type([]) and len(other) == 0:
            return self.__delslice__(i, j)

        otheri = 0
        while i < j and otheri < len(other):
            # Strict type checking.
            if type(self.dummyentry) != type(other[otheri]):
                raise TypeError
            if (len(self) > i):
                self.buflist[i] = other[otheri]
            else:
                self.append(other[otheri])
            otheri += 1
            i += 1

        self.header['size'] = len(self)

    def __reversed__(self):
        raise Exception("reverse iterator doesn't work")

    def __iter__(self):
        return self

    def next(self):
        if (self._index_ == len(self)):
            self._index_ = 0;
            raise StopIteration
        _index_ = self._index_
        self._index_ = _index_ + 1
        return self.buflist[_index_]

    def copy(self, other):
        "Copies another full buflist or just one entry."
        if issubclass(type(other), self.entryclass):
            # Only one entry was passed, so empty and then include just the one entry.
            self.__delslice__(0, len(self))
            self.append(other)
        else:
            # Assume we got a full buflist and copy it all.
            self.__delslice__(0, len(self))
            self.header.copy(other.header)
            if self.tail != None: self.tail.copy(other.tail)
            self.append(other)

    def __add__(self, other=None):
        result = self.__class__(other=self)
        result.append(other)
        return result

    def __radd__(self, other=None):
        result = self.__class__()
        result.header.copy(self.header)
        if result.tail != None: result.tail.copy(self.tail)
        result.append(other)
        result.append(self)
        return result

    def extend(self, other=None):
        return self.append(other)

    def append(self, other=None):
        "Adds another entry or another buflist"

        # None extends by one item with default values.
        if other == None: other = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)

        try:  # Try to append a single entry.
            self._append_one_entry(other)
        except:  # Maybe it's a list of entries instead.
            lst = []  # Make an alternate list.
            lst[0:] = other  # This protects against self-recursion.
            for item in lst: self._append_one_entry(item)

        self.header['size'] = len(self)

    def _append_one_entry(self, entry):
        "Deep copy one entry to the end of the list"

        # All entries must be derived from bufdict at a bare minimum.
        if issubclass(type(entry), bufdict):
            # New object same as the incoming entry.
            o = type(entry)(majorVersion=self.majorVersion, minorVersion=self.minorVersion)
        else:
            # The incoming entry is not a bufdict child. Make a default entryclass object.
            o = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)

        o.copy(entry)  # Copy by value.
        self.buflist.append(o)  # append it.

    def insert(self, index, entry=None):
        "Insert a bufdict 'entry' before 'index'"

        # None extends by one item with default values.
        if entry == None:
            entry = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)

        # Strict type checking.
        if self.strict and type(entry) != type(self.dummyentry):
            print("Can only insert an entry of type", type(self.dummyentry))
            raise TypeError

        self.buflist.insert(index, entry)
        self.header['size'] = len(self)

    def pop(self, index=None):
        "Remove and return the entry at 'index' (default last)"
        if index == None: index = self.__len__() - 1
        entry = self.buflist[index]
        del self.buflist[index]
        self.header['size'] = len(self)
        return entry

    def sort(self, key, reverse=False):
        """
        Sort the entries by 'key'.
        'reverse' is a boolean flag for descending order (default False).
        """
        sorted_list = sorted(self.buflist, key=operator.itemgetter(key), reverse=reverse)
        self.buflist = sorted_list

    def delrow(self, key, value, equal=True):
        """
        Deletes rows based on the value of a specific entry.
        'key' is the the name of the entry to check.
        'value' is the specific value to compare against.
        'equal' is a boolean flag to delete on == or !=.
            True  - Delete rows with 'key' == 'value'
            False - Delete rows with 'key' != 'value'
        """
        # Accept tokenized values.
        value = self.dummyentry.detoken(key, value)

        i = len(self)
        while i > 0:
            i -= 1
            if not ((self.buflist[i][key] == value) ^ equal):
                del (self.buflist[i])
        self.header['size'] = len(self)

    def del_row(self, tuples, equal=True):
        """
        Deletes rows based on the values of multiple entries.

        First parameter is a list of tuples.
        Each tuple in the list is (key, value).

        'equal' is a boolean flag to delete on == or !=.
            True  - Delete rows with 'key' == 'value'
            False - Delete rows with 'key' != 'value'
        """
        if equal or len(colname_value_tuple_list) <= 1:
            for k, v in tuples: self.delrow(k, v, equal)
            return

        # A match to any of the tuples will keep the row alive.
        i = len(self)
        while i > 0:
            i -= 1
            kill = True
            for k, v in tuples:
                if self.buflist[i][k] == v: kill = False
            if kill: del (self.buflist[i])

    def del_duplicates(self, keylist=None):
        "Deletes duplicate rows."
        for i in range(0, len(self)):
            if i >= len(self): break

            j = i + 1
            while j < len(self):
                if self.buflist[i].__eq__(self.buflist[j], keylist):
                    del self.buflist[j]
                    j -= 1
                j += 1

        self.header['size'] = len(self)

    def limit_row(self, key, num=10):
        """
        Limits the number of rows with unique values for the given entry.
        'key' is the the name of the entry to check.
        'num' is the number of rows allowed with the same value in the entry.
        """
        count_dict = {}
        i = 0
        while i < len(self):
            value = self.buflist[i][colname]
            if value in count_dict:
                count_dict[value] += 1
            else:
                count_dict[value] = 1
            if count_dict[value] > num:
                del self.buflist[i]
                i -= 1
            i += 1

        self.header['size'] = len(self)

    def checksum(self, buf=None, compare=None, skip=None, extra=0):
        """
        Calculate and return the check sum with the option of comparing the value.

        buf         Required byte buffer or bytearray holding data.

        compare     Optional expected value of check sum to compare against.

        skip        Optional byte index into the buffer to start checksumming.
                    Default behavior (when set to None) is to start just after
                    the position of the checksum in the header. The assumption
                    is that all content after the included checksum is checked.
                    This means we expect FW folks to install a checksum early
                    in the header of buffer payload.

        extra       Optional number of extra bytes beyond the actual list size.
                    This is only needed if the FW folks add extra data to a
                    buffer that participates in the check sum. This is rare and
                    hopefully avoided in FW implementations of test commands.
        """

        if not self.header.has_key('checksum'): return None

        if buf == None:
            buf = self.tobuf()
            checksum = self.header['checksum']

        else:
            size = self.header.bitsize('checksum')

            if skip == None:
                bitstart = self.header.bitposition('checksum')

                if bitstart % 8 != 0:
                    raise Exception("checksum must start on a byte boundary")

                skip = (bitstart + size) / 8

            checksum = None
            if size == 32:
                checksum = self.checksum32(buf, self.bytesize() + extra, skip)
            elif size == 8:
                checksum = fwChecksum8(buf, self.bytesize() + extra, skip)
            else:
                raise Exception("unrecognized checksum size")

        if compare != None and checksum != compare:
            print("CHECKSUM MISMATCH! Received 0x%X : Actual 0x%X" % (compare, checksum))

        self.header.checksum = checksum
        return checksum

    def _determine_entry_type_(self, giantInteger):
        """
        Can be overloaded with magic to figure out the entry type in a buffer.

        By overloading this method, you can peek at the buffer content to make decisions.

        The frombuf() method will first make a giant integer of the next possible entry
        in the buffer using the default entry class. As such, the default entry class
        must be suitable to make any and all decisions needed.

        Default behavior is to use the entry class we got at time of construction.
        But, you have the option of using different entry classes depending on content.
        This is the method that should figure out exactly what entry class to use on the fly.

        Another use of this method is when the host has not told use how many entries have
        been sent and is instead using an marker at the end of teh buffer. In such case,
        this method MUST be overloaded to identify taht ending marker and return None.
        You also must overload the frombuf() method and set ignoreSize True.
        """
        return self.entryclass

    def from_buf(self, buf, append=False):
        return self.frombuf(buf=buf, append=append)

    def frombuf(self, buf, append=False, overlay=False, ignoreSize=False):
        """
        Get content from a binary buffer.

        buf         Required byte buffer or bytearray. We're extracting from this buffer.

        append      Optional choice to append the new data to the list. Default False.

        overlay     Optional choice to overlay the incoming data onto of existing list entries.
                    Invented for test commands that return a list of arbitrary sized elements.
                    The host must already know what is coming out and creates the list first.
                    Then each pre-existing element of the list grabs from the buffer.
                    Only one test command uses this today (FNV peek-poke task return).
                    Only to be altered by overloading frombuf() and setting True.

        ignoreSize  Optional choice to ignore 'size' in the header for entry count.
                    Most test commands tell us how many entries are coming in the header.
                    Many do not. :/ It's a constant battle with FW folks to do it.
                    A common alternative is a marker at the end of the buffer.

                    Only meant to be altered by overloading frombuf() and setting True.
                    In such case, you MUST also overload _determine_entry_type_() to return
                    None when it finds the marker at the end of the buffer.
        """

        # Remove all existing content unless appending or overlaying.
        if not append and not overlay: self.buflist = []
        offset = self.header.frombuf(buf=buf)
        entries = self.header['size']

        # Read each entry...
        size = 0;
        while ignoreSize or size < entries:
            if overlay and size < len(self.buflist):
                # Use the existing entries to get all the data.
                offset = self.buflist[size].frombuf(buf=buf, offset=offset)
                size += 1
            else:
                # Make all new entries...
                # Use the default entry type to get the giant integer.
                giantInteger = self.dummyentry.makeGiantInteger(buf=buf, offset=offset)

                # Use magic to figure out the entry type based on content.
                newType = self._determine_entry_type_(giantInteger)

                # If we need to figure out the number of entries (ignoreSize==True),
                # _determine_entry_type_() *MUST* return None when it finds the end.
                if newType == None: break

                newEntry = newType(majorVersion=self.majorVersion, minorVersion=self.minorVersion, buf=buf, offset=offset)

                self.buflist.append(newEntry)
                size += 1
                offset += newEntry.bitsize()

        if self.tail != None: self.tail.frombuf(buf=buf, offset=offset)

        # Calculate the checksum and compare.
        if self.header.has_key('checksum'):
            self.checksum(buf, self.header['checksum'])

        self.header['size'] = len(self)

    def to_buf(self, buf=None, extra=0):
        return self.tobuf(buf=buf)

    def tobuf(self, buf=None, extra=0):
        """
        Send content to a binary buffer. Make a buffer if needed.
        If buf==None, a buf is created and returned.
        """
        if buf == None:
            buf = bytearray(self.byte_size() + extra)

        self.header['size'] = entries = len(self)
        offset = self.header.tobuf(buf=buf)

        # Send each entry...
        for i in range(0, entries):
            offset = self.buflist[i].tobuf(buf, offset)

        if self.tail != None: self.tail.tobuf(buf=buf, offset=offset)

        # Calculate a checksum if the header has one.
        if self.header.has_key('checksum'):
            self.header['checksum'] = self.checksum(buf)
            self.header.tobuf(buf)

        return buf

    def _heroic_file_load_(self, filename=None, file=None):
        """
        Virtual function to be overloaded for special handling of fromfile() failure.
        Make your own version of this if there are special files your child class uses.
        """
        raise Exception('Failed to load the file')

    def from_file(self, filename=None, file=None, append=False):
        return self.fromfile(filename=filename, file=file, append=append)

    def fromfile(self, filename=None, file=None, append=False):
        "Get content from a binary file."
        try:
            if filename != None: file = open(filename, 'rb')
            if not append: self.buflist = []

            self.header.fromfile(file=file)
            entries = self.header['size']  # Header MUST contain 'size'.

            ## Read each entry...
            for i in range(0, entries):
                temp_entry = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)
                temp_entry.fromfile(file=file)
                self.buflist.append(temp_entry)

            if self.tail != None: self.tail.fromfile(file=file)
            if filename != None: file.close()

            # Calculate the checksum and compare.
            if self.header.has_key('checksum'):
                self.checksum(None, self.header['checksum'])

            self.header['size'] = len(self)
        except:
            return self._heroic_file_load_(filename=filename, file=file)

    def from_table(self, filename=None, file=None, line_numbers=False, delimiter='\t', header=True, append=False):
        return self.fromtable(filename=filename, file=file, line_numbers=line_numbers, delimiter=delimiter, header=header, append=append)

    def fromtable(self, filename=None, file=None, line_numbers=False, delimiter='\t', header=True, append=False):
        "Get content from a table file"

        if (filename != None): file = open(filename)
        if (not append): self.buflist = []

        # Skip the header line
        if header:
            line = file.readline()
            line = line.rstrip()
            values = line.split(delimiter)

            # line numbers or not?
            if values[0] == "line":
                line_numbers = True

        # Don't try to pull in line numbers.
        if line_numbers:
            first_column = 1
        else:
            first_column = 0

        for line in file:
            line = line.rstrip()
            values = line.split(delimiter)

            entry = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)
            temp_entry = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)

            column = first_column

            # Copy the values into the entry
            for key in self.keys():
                temp_entry[key] = values[column]
                column += 1

            self.buflist.append(temp_entry)

    def to_file(self, filename):
        return self.tofile(filename=filename)

    def tofile(self, filename):
        "Send content to a binary file"
        file = open(filename, 'wb')
        buf = self.tobuf()
        s = "".join([chr(x) for x in buf])
        file.write(s)
        file.close()

    def describe(self):
        "Prints the description list"

        print("Header:\n")
        self.header.describe()
        print("Entry:\n")
        self.dummyentry.describe(header=False)

        if self.tail != None:
            print("Tail:\n")
            self.tail.describe(header=False)

    def __repr__(self):
        return str(self)

    def __str__(self, delimiter='\n', list_delimiter=None, header_delimiter=None, show_names=True,
                show_index=True, indexsize=5, raw=None, offset=0):
        self.checksum()
        mystring = ''
        mystring += self.__name__ + ':\n'
        mystring += self.header.__str__(header=False)

        if header_delimiter != None: mystring += header_delimiter
        indexformat = "%%%dd " % (indexsize)

        for i in range(len(self.buflist)):
            if show_index == True: mystring += indexformat % (i + offset)
            if show_names == True: mystring += "%s" % (self.buflist[i].__name__)
            mystring += delimiter + self.buflist[i].__str__(header=False, raw=self.raw)
            if list_delimiter != None: mystring += list_delimiter

        if self.tail != None: mystring += "TAIL:\n" + self.tail.__str__(header=False)

        return mystring

    def table(self, delimiter='\t', header=True, show_line_numbers=False):
        "Return a string with contents in table form."
        mystring = ''
        if header:
            if show_line_numbers == True:
                mystring += 'line' + delimiter

            for key in self.dummyentry:
                mystring += key + delimiter

            mystring += '\n'

        for i in range(0, len(self.buflist)):
            if show_line_numbers == True:
                mystring += str(i) + delimiter

            for key in self.dummyentry:
                mystring += self.buflist[i].item_string(key, valueSize=self.valuesize) + delimiter

            mystring += '\n'

        return mystring

    def table_to_file(self, filename=None, file=None, delimiter='\t', header=True, append=False, show_line_numbers=False):
        self.tabletofile(filename=filename, file=file, delimiter=delimiter, header=header, append=append, show_line_numbers=show_line_numbers)

    def tabletofile(self, filename=None, file=None, delimiter='\t', header=True, append=False, show_line_numbers=False):
        "Send content to a file in table form."
        if append: header = False
        if (filename != None):
            if (append):
                file = open(filename, 'a')
            else:
                file = open(filename, 'w')
        file.write(self.table(delimiter=delimiter, header=header, show_line_numbers=show_line_numbers))
        if (filename != None): file.close()

    def table_from_file(self, filename=None, file=None, delimiter='\t', header=True, append=False):
        return self.tablefromfile(filename=filename, file=file, delimiter=delimiter, header=header, append=append)

    def tablefromfile(self, filename=None, file=None, delimiter='\t', header=True, append=False):
        if (filename != None): file = open(filename, 'rb')
        if (not append): self.buflist = []

        lines = []
        for line in file: lines.append(line.rstrip())

        if header:
            keys = lines[0].split(delimiter)
            idx = 1
        else:
            keys = self.dummyentry.keys()
            idx = 0

        for i in range(idx, len(lines)):
            temp_entry = self.entryclass(majorVersion=self.majorVersion, minorVersion=self.minorVersion)
            data = lines[i].split(delimiter)
            if len(data) < len(keys): continue

            j = 0
            for key in keys:
                item = data[j]
                j = j + 1

                if item.decode().isnumeric():
                    value = long(item)
                else:
                    if item[0] == '0' and ((item[1] == 'x') or (item[1] == 'X')):
                        value = long(item, 16)
                    else:
                        value = item

                temp_entry[key] = value

            self.buflist.append(temp_entry)

        if (filename != None): file.close()
        self.checksum()
        self.header['size'] = len(self)

    def bitsize(self):
        "Bits taken in a buffer by the entire object"
        bitsize = self.header.bitsize()
        for i in range(len(self.buflist)): bitsize += self.buflist[i].bitsize()
        if self.tail != None: bitsize += self.tail.bitsize()
        return bitsize

    def byte_size(self):
        return self.bytesize()

    def bytesize(self):
        "Bytes taken in a buffer by the entire object"
        return int(math.ceil(self.bitsize() / 8.0))

    def txt_to_file(self, filename=None, file=None, append=False):
        "Send content to a human-readable text file"
        return self.txttofile(filename=filename, file=file, append=append)

    def txttofile(self, filename=None, file=None, append=False):
        "Send content to a human-readable text file"
        if (filename != None):
            if (append):
                file = open(filename, 'a')
            else:
                file = open(filename, 'w')
        print >> file, str(self)
        if (filename != None): file.close()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __eq__(self, other):
        if type(other) is type(self):
            if self.header != other.header: return False
            if self.buflist != other.buflist: return False
            if self.tail != other.tail: return False
            return True
        else:
            return False


def with_attributes(cls):
    if hasattr(cls, "DESCRIPTION"):
        descr = cls.DESCRIPTION

        for e in range(0, len(descr), bdFIELDS):
            name = descr[e + bdNAME]

            getFun = get_attr_factory(name)
            setFun = set_attr_factory(name)

            prop = property(fget=getFun, fset=setFun)
            setattr(cls, name, prop)

    return cls


def get_attr_factory(attr):
    def get_attr(self):
        return self.__getitem__(key=attr)

    return get_attr


def set_attr_factory(attr):
    def set_attr(self, val):
        return self.__setitem__(key=attr, value=val)

    return set_attr


import collections

bdDescriptionEntry = collections.namedtuple("bdDescriptionEntry", ["name", "size", "signed", "default", "style", "tokens", "help"])


def splitDescription(desc):
    return [bdDescriptionEntry(*(desc[n:n + bdFIELDS])) for n in range(0, len(desc), bdFIELDS)]


#     name                  size           signed default style Tokens  help string

def intStringLengthByBits(n):
    return len(str(-(1 << n)))


def getPrintFormatStrFromDescription(desc, indexSlot=False):
    # desc = splitDescription(desc)
    indexStr = ["{:>5}"] if indexSlot else []

    def getLength(descLine):
        return max(len(descLine.name), intStringLengthByBits(descLine.size), 4)  # 4 in case "None"

    formatStrs = indexStr + ["{:>%d}" % getLength(d) for d in desc]
    return "  ".join(formatStrs) + "\n"
