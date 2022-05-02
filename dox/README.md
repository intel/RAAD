# Sphinx Generator for Linux

A simple generator for using Sphinx to document small Python modules.

reStructured Text cheat sheet: [http://github.com/#index](http://github.com/#index)

Python documentation cheat sheet: [`module/__init__.py`](module/__init__.py)

## Installation

    $ sudo apt-get install python-sphinx
    $ sudo pip install sphinx
    # Depends on which version you prefer ...
    $ sudo pip3 install sphinx

## Quickstart

Sphinx offers an easy quickstart:

    $ mkdir docs
    $ cd docs
    # Quickstart, select yes for apidoc and mathjax and for splitting build and source.
    $ sphinx-quickstart
    $ sphinx

Choose to separate source and build directories, choose project name and version and the autodoc extension.

If the code/module to be documentation is accessible from the root directory, edit `docs/source/conf.py` as follows:

    import os
    import sys
    sys.path.insert(0, os.path.abspath('../../'))

Then the modules can be automatically documented using:

    $ sphinx-apidoc -f -o source/ ../
    $ make html

## Python 2.x

For modules or dependencies not supporting Python 3, `docs/Makefile` can ba adapted:

    SPHINXBUILD   = python -c "import sys,sphinx;sys.exit(sphinx.main(sys.argv))"

## Instruction Commands

New development should have a unit test capability built in to ensure there are no regressions.

* Auto doxygen location
    * RAAD\dox\build\index.html
* Docstring Style
    * https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html
* Example documentation execute order:
    * `cd RAAD\dox\source\`
    * `python findClasses.py`
    * `cd ..`
    * `make clean`
    * `make html`
