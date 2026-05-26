# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
# docs/conf.py
import os
import sys
import django

# Добавляем путь к проекту
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../core'))

# Настройки Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'testdjango.settings'
django.setup()

project = 'MSHP Answers'
copyright = '2026, MSHP students'
author = 'MSHP students'
release = '1.0'
version = '1.0'

# Расширения Sphinx
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.todo',
    'sphinx.ext.graphviz',
    'sphinx.ext.inheritance_diagram',
]

# Тема оформления
html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
html_theme_options = {
    'navigation_depth': 4,
    'sticky_navigation': True,
    'logo_only': False,
}

# Язык
language = 'ru'

# Исключения
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# Настройка autodoc
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True,
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True

todo_include_todos = True