#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: Benjamin Vial
# This file is part of gyptis
# Version: 1.0.2
# License: MIT
# See the documentation at gyptis.gitlab.io

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#


import os
import sys
from datetime import date

import pyvista
import sphinx_gallery
from pybtex.plugin import register_plugin
from pybtex.style.formatting.unsrt import Style as UnsrtStyle
from pybtex.style.labels import BaseLabelStyle

import gyptis as package

# necessary when building the sphinx gallery
pyvista.BUILDING_GALLERY = True
pyvista.OFF_SCREEN = True

# Optional - set parameters like theme or window size
pyvista.set_plot_theme("document")
# -- General configuration ------------------------------------------------

# If your documentation needs a minimal Sphinx version, state it here.
#
# needs_sphinx = '1.0'

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autosummary",
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    # "sphinx.ext.doctest",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    # 'sphinx.ext.todo',
    # 'sphinx.ext.coverage',
    # "sphinx.ext.mathjax",
    "sphinxcontrib.bibtex",
    "sphinxcontrib.rsvgconverter",
    "sphinx_gallery.gen_gallery",
    "sphinx_copybutton",
    # 'sphinx_issues',
]


# a simple label style which uses the bibtex keys for labels
class MatchLabelStyle(BaseLabelStyle):
    def format_labels(self, sorted_entries):
        for entry in sorted_entries:
            yield entry.key


class GyptisStyle(UnsrtStyle):
    default_label_style = MatchLabelStyle


register_plugin("pybtex.style.formatting", "gyptisstyle", GyptisStyle)

bibtex_bibfiles = ["_custom/latex/biblio.bib"]
bibtex_default_style = "gyptisstyle"
bibtex_reference_style = "label"
# this is needed for some reason...
# see https://github.com/numpy/numpydoc/issues/69
numpydoc_class_members_toctree = False
numpydoc_show_class_members = False

autodoc_default_options = {"inherited-members": None}


autosummary_generate = True
# import glob
# autosummary_generate = glob.glob("*.rst")

add_function_parentheses = False


# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
# You can specify multiple suffix as a list of string:
#
# source_suffix = ['.rst', '.md']
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = package.__name__
author = package.__author__
copyright = f"{date.today().year}, {author}"


host = "gitlab"


html_context = {
    "description": package.__description__,
    "show_fork": True,
    "repo": f"{package.__name__}/{package.__name__}",
    "show_pip_install": True,
    "pipname": package.__name__,
    "dockername": f"{package.__name__}/{package.__name__}",
}


# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The short X.Y version.
version = package.__version__
# The full version, including alpha/beta/rc tags.
release = package.__version__  # + '-git'

# default_role = 'py:obj'
# The language for content autogenerated by Sphinx. Refer to documentation
# for a list of supported languages.
#
# This is also used if you do content translation via gettext catalogs.
# Usually you set "language" from the command line for these cases.
language = "en"

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This patterns also effect to html_static_path and html_extra_path
exclude_patterns = ["_custom", "_build", "Thumbs.db", ".DS_Store"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# If true, `todo` and `todoList` produce output, else they produce nothing.
todo_include_todos = True

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"
highlight_language = "python3"


# -- Options for HTML output ----------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.

html_theme = "pydata_sphinx_theme"

html_static_path = ["_custom/static"]


def env_get_outdated(app, env, added, changed, removed):
    return ["index"]


def setup(app):
    app.connect("env-get-outdated", env_get_outdated)
    app.add_css_file("css/custom_styles.css")
    app.add_css_file("css/custom_gallery.css")
    app.add_css_file("css/custom_pygments.css")
    app.add_js_file("js/custom.js")


# Theme options are theme-specific and customize the look and feel of a theme
# further.  For a list of options available for each theme, see the
# documentation.
#
# html_theme_options = {}
# Theme options are theme-specific and customize the look and feel of a
# theme further.
html_theme_options = {
    "show_toc_level": 3,
    "show_prev_next": False,
    "show_nav_level": 2,
    "navbar_end": ["navbar-icon-links"],
    "logo": {
        "image_light": "_assets/gyptis-name.png",
    },
}


# The name for this set of Sphinx documents.  If None, it defaults to
# "<project> v<release> documentation".
html_title = "__WEBPAGE_TITLE_PLACEHOLDER__"

# A shorter title for the navigation bar.  Default is the same as html_title.
# html_short_title = "Demo"

# (Optional) Logo. Should be small enough to fit the navbar (ideally 24x24).
# Path should be relative to the ``_static`` files directory.
html_logo = "./_assets/gyptis-name.png"
# html_logo = ""

# The name of an image file (within the static path) to use as favicon of the
# doc.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = "./_assets/gyptis.png"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ["_static"]

# If not '', a 'Last updated on:' timestamp is inserted at every page bottom,
# using the given strftime format.
# html_last_updated_fmt = '%b %d, %Y'

# If true, SmartyPants will be used to convert quotes and dashes to
# typographically correct entities.
# html_use_smartypants = True
# Custom sidebar templates, maps document names to template names.


html_sidebars = {
    "examples": [],
    "tutorials": [],
    "changelog": [],
}

# html_sidebars = {'examples': ['localtoc.html']}
# Additional templates that should be rendered to pages, maps page names to
# template names.
html_additional_pages = {"index": "home.html"}

# If false, no module index is generated.
# html_domain_indices = True

# If false, no index is generated.
# html_use_index = True

# If true, the index is split into individual pages for each letter.
# html_split_index = False

# If true, links to the reST sources are added to the pages.
# html_show_sourcelink = True

# If true, "Created using Sphinx" is shown in the HTML footer. Default is True.
html_show_sphinx = False

# If true, "(C) Copyright ..." is shown in the HTML footer. Default is True.
html_show_copyright = True

# If true, an OpenSearch description file will be output, and all pages will
# contain a <link> tag referring to it.  The value of this option must be the
# base URL from which the finished HTML is served.
# html_use_opensearch = ''

# This is the file name suffix for HTML files (e.g. ".xhtml").
# html_file_suffix = None

# -- Options for HTMLHelp output ------------------------------------------

# Output file base name for HTML help builder.
htmlhelp_basename = f"{package.__name__}_doc"


# -- Options for LaTeX output ---------------------------------------------

# latex_elements = {
#     # The paper size ('letterpaper' or 'a4paper').
#     #
#     # 'papersize': 'letterpaper',
#     # The font size ('10pt', '11pt' or '12pt').
#     #
#     # 'pointsize': '10pt',
#     # Additional stuff for the LaTeX preamble.
#     #
#     # 'preamble': '',
#     # Latex figure (float) alignment
#     #
#     # 'figure_align': 'htbp',
# }


latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #
    "papersize": "a4paper",
    # The font size ('10pt', '11pt' or '12pt').
    #
    "pointsize": "10pt",
    # Additional stuff for the LaTeX preamble.
    "preamble": r"""
       \usepackage{gyptis}
        \renewcommand{\subtitle}{%s}

        """
    % (package.__description__),
    # Latex figure (float) alignment
    #
    # 'figure_align': 'htbp',
}


# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    (
        master_doc,
        f"{package.__name__}.tex",
        "Documentation",
        package.__author__,
        "manual",
    )
]
# latex_docclass = {
#    'manual': 'gyptis',
# }
latex_additional_files = [
    "_custom/latex/gyptis.sty",
]

latex_logo = html_logo

# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [
    (
        master_doc,
        package.__name__,
        f"{package.__name__} Documentation",
        [author],
        1,
    )
]


# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        master_doc,
        package.__name__,
        f"{package.__name__} Documentation",
        author,
        package.__name__,
        package.__description__,
        "Science/Engineering",
    )
]


# Example configuration for intersphinx: refer to the Python standard library.

intersphinx_mapping = {
    "python": ("https://docs.python.org/{.major}".format(sys.version_info), None),
    "numpy": ("https://numpy.org/doc/stable/", None),
    "matplotlib": ("https://matplotlib.org/", None),
    "scipy": ("https://docs.scipy.org/doc/scipy/reference/", None),
    "gyptis": ("https://gyptis.gitlab.io/", None),
}


sphinx_gallery_conf = {
    # path to your examples scripts
    "examples_dirs": ["../examples", "../tutorials"],
    # path where to save gallery generated examples
    "gallery_dirs": ["examples", "tutorials"],
    # # path to your examples scripts
    # "examples_dirs": ["../tutorials"],
    # # path where to save gallery generated examples
    # "gallery_dirs": ["tutorials"],
    # directory where function granular galleries are stored
    "backreferences_dir": "generated/backreferences",
    "remove_config_comments": True,
    "reference_url": {
        "sphinx_gallery": None,
    },
    "reset_modules": (),
    "image_scrapers": ("pyvista", "matplotlib"),
    # "pypandoc": True,
    # "pypandoc": {"extra_args": ["-C","--bibliography=_custom/latex/biblio.bib"], "filters": []},
    # "filename_pattern": "plot_homogenization\.py",
    "filename_pattern": "/plot_",
    "ignore_pattern": r"^((?!/plot_).)*$",  # ignore files that do not start with plot_
    # "first_notebook_cell": (
    #     "import matplotlib\n" "mpl.style.use('gyptis')\n" "%matplotlib inline"
    # ),
    # "image_scrapers": ("matplotlib", PNGScraper()),
    # Modules for which function level galleries are created.
    "doc_module": package.__name__,
    "thumbnail_size": (800, 800),
    "default_thumb_file": "./_assets/gyptis.png",
    "show_memory": True,
    "first_notebook_cell": (
        "# This file is part of gyptis\n" "# License: MIT\n" "%matplotlib notebook"
    ),
    "last_notebook_cell": ("import gyptis.utils.jupyter\n" "%gyptis_version_table"),
    "binder": {
        "org": "gyptis",
        "repo": "gyptis.gitlab.io",
        "branch": "doc",
        "binderhub_url": "https://mybinder.org",
        "dependencies": "../environment.yml",
        "notebooks_dir": "notebooks",
        "use_jupyter_lab": False,
    },
}
