# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0, os.path.abspath('../..'))

from src import __metadata__ as md

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = md.__project__
copyright = md.__copyright_short__.replace('Copyright', '').strip(' ')
author = md.__author__
release = md.__version__

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
	'sphinx.ext.duration',
	'sphinx.ext.doctest',
	'sphinx.ext.autodoc',
	'sphinx.ext.autosummary',
	'sphinx.ext.inheritance_diagram',
	'sphinx.ext.napoleon',
	'sphinx.ext.viewcode',
	'sphinx.ext.autosectionlabel',
	'sphinx_copybutton',
    'myst_nb',
]

templates_path = ['_templates']
exclude_patterns = ['.ipynb_checkpoints/*']


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'furo'
html_static_path = ['_static']
