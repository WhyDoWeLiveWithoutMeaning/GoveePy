# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

# autodoc_mock_imports = ["Govee", "GoveeLocal"]

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'GoveePy'
copyright = '2023, Meaning'
author = 'Meaning'
release = '1.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc'
]

templates_path = ['_templates']
exclude_patterns = []

autodoc_default_options = {
    'ignore-module-all': True,
    'members': True,
    'undoc-members': True,
    'show-inheritance': False,
    'private-members': False,
    'member-order': 'bysource',
    'exclude-members': '__dict__,__weakref__,__module__,abstractmethod'
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
