from __future__ import division, print_function, unicode_literals

import os
import sys

import sphinx_rtd_theme
from recommonmark.parser import CommonMarkParser

sys.path.insert(0, os.path.abspath('..'))
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.abspath('_ext'))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.doctest',
    'sphinx.ext.intersphinx',
    'sphinx.ext.todo',
    'sphinx.ext.coverage',
    'sphinx.ext.mathjax',
    'sphinx.ext.ifconfig',
    'sphinx.ext.viewcode',
]
templates_path = ['_templates']

source_suffix = '.rst'

master_doc = 'index'
project =  u'Stacker'
copyright = '2017, Shahar Azulay, Ariel Hanemann'

version = '1.0'
release = '1.0'
exclude_patterns = ['_build']
default_role = 'obj'

htmlhelp_basename = 'Stacker'
latex_documents = [
    (master_doc, 'Stacker.tex', u'Stacker Documentation',
     u'Shahar Azulay, Ariel Hanemann', 'manual'),
]
man_pages = [
    (master_doc, 'stacker', u'Stacker Documentation',
     [u'Shahar Azulay, Ariel Hanemann'], 1)
]

exclude_patterns = [
    # 'api' # needed for ``make gettext`` to not die.
]


#---- HTML OUTPUT CONFIG ----
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
# html_theme = "guzzle_sphinx_theme"

# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
html_theme_options = {
    'github_user': 'shaharazulay',
    'github_repo': 'stacker',
    'github_button': True,
    'github_banner': True,
    'page_width': '100%',
    'sidebar_width': '20%',
}

html_logo = '_static/logo.png'
html_favicon = '_static/logo.ico'
html_static_path = ['_static']

# Activate autosectionlabel plugin
autosectionlabel_prefix_document = True
