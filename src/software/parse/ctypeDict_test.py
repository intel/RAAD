#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Randal Eike, Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
from src.software.parse.internal import twidlDictGen
import pprint


def main():
    myObjInstance = None
    dictionary = twidlDictGen.datacontrolDict()


    print("==Printing Dictionary==\n")
    pprint.pprint(dictionary)

    print("==Accessing Class Struct in Dictionary==\n")
    myObj = dictionary[6].ctypeStructure
    print(myObj)

    print("==Instantiating class from dictionary==\n")
    exec("myObjInstance = %s()"%(myObj))
    print(myObjInstance)


if __name__ == "__main__":
    main()
