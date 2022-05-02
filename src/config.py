#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from __future__ import absolute_import, division, print_function, unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations
import sys, os, datetime, traceback, optparse


def main():
    ##############################################
    # Main function, Options
    ##############################################
    parser = optparse.OptionParser()
    parser.add_option("--example", action='store_true', dest='example', default=False,
                      help='Show command execution example.')
    parser.add_option("--debug", action='store_true', dest='debug', default=True, help='Debug mode.')
    (options, args) = parser.parse_args()
    print("Settings")
    print(f"{options}")
    print(f"{args}")
    ##############################################
    # Main
    ##############################################
    return 0


if __name__ == '__main__':
    print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__, __name__, str(__package__)))
    print("Path before \n{0}".format(os.environ['PATH']))
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    print("Path after \n{0}".format(os.environ['PATH']))
    """Performs execution delta of the process."""
    p = datetime.datetime.now()
    try:
        main()
    except Exception as e:
        print("Fail End Process: ", e)
        traceback.print_exc()
    q = datetime.datetime.now()
    print("Execution time: " + str(q - p))
