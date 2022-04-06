# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

import os
import sys
from importlib.metadata import version as imp_version
sys.path.insert(0, os.path.abspath('../'))


project = 'Quart-Schema'
copyright = '2020, Philip Jones'
author = 'Philip Jones'
version = imp_version("quart-schema")
release = version

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon']

source_suffix = '.rst'

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

html_theme_options = {
    "external_links": [
        {"name": "Source code", "url": "https://github.com/pgjones/quart-schema"},
        {"name": "Issues", "url": "https://github.com/pgjones/quart-schema/issues"},
    ],
    "icon_links": [
        {
            "name": "Github",
            "url": "https://github.com/pgjones/quart-schema",
            "icon": "fab fa-github",
        },
    ],
}
