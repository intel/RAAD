#!/usr/bin/env sh
# Method 1
# conda create --name radPy --file anacondaPackages.txt
# Method 2
# conda env create -f environment.
# Method 3 Recrease from existing
conda env update -f environment.yml
