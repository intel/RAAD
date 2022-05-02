#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
## @package axon
from __future__ import absolute_import, division, print_function, \
    unicode_literals  # , nested_scopes, generators, generator_stop, with_statement, annotations

# Standard Classes
import os, configparser

# Created Classes


"""
Brief:
    
"""

PROFILE_DESCRIPTION = {
    "-download.choice.time-": "timeStamp",
    "-download.choice.product-": "product",
    "-download.choice.serial-": "serial",
    "-download.choice.user-": "host"
}


class AxonProfile(object):

    def __init__(self, profile_path=os.getcwd(), profile_description=None, profileFile=None):
        if profile_description is None:
            profile_description = PROFILE_DESCRIPTION
        self.profile_path = profile_path
        self.profile_description = profile_description
        self.config = configparser.ConfigParser()
        self.profileFile = profileFile

    def GetProfile(self, profileFile='.raadProfile/axonProfile.ini'):
        """
        Get config parser and reads the already-created file if it exists
        Returns:
            configParser: configParser that can parse the formats from .ini files
        """
        profileFile = os.path.abspath(os.path.join(os.getcwd(), profileFile))
        # Check if file exists and read in the dictionary
        if self.profileFile is None:
            proFile = profileFile
        else:
            proFile = self.profileFile

        if os.path.exists(proFile):
            # if self.debug: print("profile: ", proFile)
            self.config.read(proFile)

        axonIDs = self.config.sections()

        return axonIDs, self.config

    def AddSection(self, entry, ID):
        """

        Returns:

        """
        # Add a section header for the id
        self.config.add_section(ID)

        # Populate data for the
        for option in sorted(self.profile_description.keys()):
            self.config.set(ID, option, str(entry[self.profile_description[option]]))

        return

    def SaveProfile(self, profileFile='.raadProfile/axonProfile.ini'):
        profileFile = os.path.abspath(os.path.join(os.getcwd(), profileFile))
        # Check if file exists and read in the dictionary
        if self.profileFile is None:
            proFile = profileFile
        else:
            proFile = self.profileFile

        if os.path.exists(proFile):
            with open(proFile, 'w+') as axonFile:
                self.config.write(axonFile)
        return
