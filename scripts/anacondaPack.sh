#!/usr/bin/env sh
# Pack environment located at an explicit path into radPy.tar.gz
# conda pack -p /explicit/path/to/radPy
#
# Pack environment my_env into radPy.tar.gz
conda pack -n radPy -o radPy.tar.gz

