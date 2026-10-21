# Sphinx configuration: https://www.sphinx-doc.org/en/master/usage/configuration.html

import Pyjo.Reactor.Twisted

import inspect
import os
import tomllib


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# The module is imported from the environment of uv sync, where the project is installed in editable mode, with
# Pyjoyment and Twisted, which it imports
with open(os.path.join(ROOT, 'pyproject.toml'), 'rb') as f:
    PROJECT = tomllib.load(f)['project']

project = PROJECT['name']
author = ', '.join(a['name'] for a in PROJECT['authors'])
copyright = f'2026, {author}'
version = release = Pyjo.Reactor.Twisted.__version__

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx']

# The modules of Pyjoyment, as Pyjo.Reactor.Poll, are links to its documentation
intersphinx_mapping = {
    'pyjoyment': ('https://pyjoyment.readthedocs.io/en/latest/', None),
}


# A class under a second name, as `object`, or a method of the class as a function of the module, as `new`, is an alias
# that is not documented twice: the class documents it under its own name.
def skip_alias(app, what, name, obj, skip, options):
    if what == 'module' and (inspect.ismethod(obj) or isinstance(obj, type) and obj.__name__ != name):
        return True
    return None


def setup(app):
    app.connect('autodoc-skip-member', skip_alias)


# The table of contents lists the page, not the classes and functions that autodoc documents on it.
toc_object_entries = False

exclude_patterns = ['_build']

html_theme = 'alabaster'
html_theme_options = {
    'github_user': 'dex4er',
    'github_repo': 'Pyjo-Reactor-Twisted',
    'show_powered_by': False,
    # The sans-serif font of the system, where Alabaster has Georgia, as in Pyjoyment
    'font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    'head_font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
}
