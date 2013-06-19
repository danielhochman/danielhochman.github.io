#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'Daniel Hochman'
SITENAME = u'/var/log/danielhochman'
SITEURL = 'http://localhost:8000'

TIMEZONE = 'America/Los_Angeles'

DEFAULT_LANG = u'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

DEFAULT_PAGINATION = 1

MENUITEMS = (
    ('Archives', '/archives.html'),
)
DISPLAY_PAGES_ON_MENU = True

FILES_TO_COPY = (
    ('extra/favicon.ico', 'favicon.ico'),
)

THEME = 'themes/pelican-foundation-mod'
# THEME = 'pelican-foundation'

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
