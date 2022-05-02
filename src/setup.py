#!/usr/bin/python3
# -*- coding: utf-8 -*-
# *****************************************************************************/
# * Authors: Joseph Tarango
# *****************************************************************************/
from setuptools import setup, find_packages

setup(name='RAAD',
      version='1.0',
      description="NVMe telemetry data analysis tools",
      long_description='Telemetry is the state space snapshot which tightly-couple specialists to pertinent data, remotely, '
                  'removing the cyber-physical challenges with interacting on complex platforms. The immediate benefit '
                  'is precise and rapid data extraction correlated to customer platforms. The purposeful subsequent '
                  'benefit is reactive-proactive real-time analytics for monitoring of client platforms and data '
                  'centers. The real-time processing of the data enables data mining, machine learning, and artificial '
                  'intelligence. The application of these techniques is given in an instance of Intel SSDs and can be '
                  'applied to technological eco-systems.',
      classifiers=[
          "Development Status :: 2 - Pre-Alpha",  # https://pypi.org/classifiers/
          "Environment :: Console",
          "Operating System :: POSIX :: Linux",
          # "Operating System :: Microsoft :: Windows",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Unix Shell",
          "LICENSE :: OSI APPROVED :: APACHE SOFTWARE LICENSE"],
      keywords='telemetry monitoring',
      author='Joseph_Tarango',
      author_email='nil@nil.nil',
      license='APL 2.0',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      url='https://github.com/intel/RAAD.git',
      platforms=['linux'],  # , 'win32'],
      install_requires=[],
      )
