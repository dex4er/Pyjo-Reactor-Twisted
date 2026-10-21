# Sphinx configuration: https://www.sphinx-doc.org/en/master/usage/configuration.html

import Pyjo.Reactor.Twisted

import functools
import inspect
import os
import subprocess
import sys
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

extensions = ['sphinx.ext.autodoc', 'sphinx.ext.intersphinx', 'sphinx.ext.linkcode']

# The modules of Pyjoyment, as Pyjo.Reactor.Poll, are links to its documentation
intersphinx_mapping = {
    'pyjoyment': ('https://pyjoyment.readthedocs.io/en/latest/', None),
}

# The commit that the links to the source point to: the one that Read the Docs builds, or the one of the checkout
COMMIT = (
    os.environ.get('READTHEDOCS_GIT_COMMIT_HASH')
    or subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    or 'main'
)


# The link [source] of a class, a function or a method goes to the lines of its source on GitHub; an object of
# Pyjoyment, as a method that the class inherits, has none, as its source is not in this repository
def linkcode_resolve(domain, info):
    if domain != 'py' or not info['module']:
        return None
    obj = sys.modules.get(info['module'])
    for part in info['fullname'].split('.'):
        obj = getattr(obj, part, None)
    if isinstance(obj, property):
        obj = obj.fget
    elif isinstance(obj, functools.cached_property):
        obj = obj.func
    try:
        obj = inspect.unwrap(obj)
        path = inspect.getsourcefile(obj)
        lines, start = inspect.getsourcelines(obj)
    except (TypeError, OSError, ValueError):
        return None
    if not path or not os.path.abspath(path).startswith(ROOT + os.sep):
        return None
    file = os.path.relpath(path, ROOT).replace(os.sep, '/')
    return f'https://github.com/dex4er/Pyjo-Reactor-Twisted/blob/{COMMIT}/{file}#L{start}-L{start + len(lines) - 1}'


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
    # The way back to the documentation of Pyjoyment, whose project this one is a subproject of on Read the Docs
    'extra_nav_links': {
        'Pyjoyment': 'https://pyjoyment.readthedocs.io/en/latest/',
        'Distributions': 'https://pyjoyment.readthedocs.io/en/latest/distributions.html',
    },
    # The sans-serif font of the system, where Alabaster has Georgia, as in Pyjoyment
    'font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    'head_font_family': "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
}
