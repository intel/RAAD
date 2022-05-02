# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

print(sys.executable)

project = 'AutoPerf'
copyright = '2021, Mejbah Alam, Justin Gottschlich, Nesime Tatbul, Javier Turek, Timothy Mattson, Abdullah Muzahid, Bradley MacDonald, Niranjan Hasabnis, Joseph Tarango'
author = 'Mejbah Alam, Justin Gottschlich, Nesime Tatbul, Javier Turek, Timothy Mattson, Abdullah Muzahid, Bradley MacDonald, Niranjan Hasabnis, Joseph Tarango'

release = '1.0'

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.todo', 'sphinx.ext.viewcode', 'sphinx.ext.coverage', 'sphinx.ext.napoleon', 'sphinx_autodoc_typehints', 'sphinx_rtd_theme', 'sphinx.ext.autosectionlabel']

set_type_checking_flag = True

templates_path = ['_templates']

exclude_patterns = []

html_theme = 'sphinx_rtd_theme'

html_static_path = []
