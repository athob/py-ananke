# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

package_name = 'ananke'

import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath('../..'))

import index_toc
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
    'sphinx_math_dollar',
    'sphinx.ext.mathjax',
    'sphinx.ext.duration',
    'sphinx.ext.doctest',
    'sphinx.ext.autodoc',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.autosectionlabel',
    'sphinx_copybutton',
    'myst_nb',
]

exclude_patterns = ['.ipynb_checkpoints/*']

napoleon_use_param = False

nb_execution_timeout = 100

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme' # 'furo'

# -- Options for automatic API doc

autodoc_default_options = {
    'member-order': 'bysource',
    'special-members': '__init__',
    'ignore-module-all': True
}

def run_apidoc(_):
    try:
        from sphinx.ext.apidoc import main
    except ImportError:
        from sphinx.apidoc import main

    sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
    cur_dir = os.path.abspath(os.path.dirname(__file__))

    api_doc_dir = os.path.join(cur_dir, "modules")
    module = os.path.join(cur_dir, "../..", f"src/{package_name}")
    ignore = [
    ]

    main(["-M", "-f", "-e", "-T", "-d 0", "-o", api_doc_dir, module, *ignore])


def setup(app):
    app.connect("builder-inited", run_apidoc)
