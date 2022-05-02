#!/usr/bin/env sh
# Unpack environment into directory `my_env`
mkdir -p radPy
tar -xzf radPy.tar.gz -C my_env

# Use Python without activating or fixing the prefixes. Most Python
# libraries will work fine, but things that require prefix cleanups
# will fail.
./radPy/bin/python

# Activate the environment. This adds `my_env/bin` to your path
source radPy/bin/activate

# Run Python from in the environment
# python
#
# Cleanup prefixes from in the active environment.
# Note that this command can also be run without activating the environment
# as long as some version of Python is already installed on the machine.
# conda-unpack
