# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os, sys, fnmatch

excludesList = [".", "_", "__", "*external*", "__pycache__", "__init__.py", '*__.py']
includesList = ['*.py']

rootPathDir = os.path.abspath('../../src')
sys.path.insert(0, rootPathDir)
print("Root Path Directory {}".format(rootPathDir))

rootPathDir = os.path.abspath('../../')
sys.path.insert(0, rootPathDir)
print("Root Path Directory {}".format(rootPathDir))


def _filter(paths):
    matches = []

    for path in paths:
        append = None

        for include in includesList:
            if os.path.isdir(path):
                append = True
                break

            if fnmatch.fnmatch(path, include):
                append = True
                break

        for exclude in excludesList:
            if os.path.isdir(path) and path == exclude:
                append = False
                break

            if fnmatch.fnmatch(path, exclude):
                append = False
                break

        if append:
            matches.append(path)

    return matches
    
def addAll():
    rootPathDir = os.path.abspath('../../')
    print("Root Path Directory {}".format(rootPathDir))

    sourceList = []
    for root, dirs, files in os.walk(rootPathDir):
        dirs[:] = _filter(map(lambda d: os.path.join(root, d), dirs))
        files[:] = _filter(map(lambda f: os.path.join(root, f), files))

        for filename in files:
            filename = os.path.join(root, filename)
            print("Added Path Directory {}".format(filename))
            sourceList.append(filename)

    for sourceFile in sourceList:
        sys.path.insert(0, os.path.abspath(sourceFile))


# -- Project information -----------------------------------------------------

project = 'RAAD'
copyright = '2022, Joseph Tarango'
author = 'Joseph Tarango'

version = '1.0'

release = 'Alpha'

extensions = [
    'sphinx.ext.autosummary',
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.githubpages',
    'sphinx.ext.todo',
    'sphinx.ext.mathjax',
    'sphinx.ext.napoleon',
]

napoleon_google_docstring = False

templates_path = ['_templates']

source_suffix = ['.rst', '.md']

master_doc = 'index'

exclude_patterns = []

todo_include_todos = True

html_theme = 'alabaster'