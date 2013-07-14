#!/usr/bin/env python

import gettext
import locale

import config

gettext.install('messages', 'locale')
locale.setlocale(locale.LC_TIME, '')

restarting = False
quiting = False

# vim: et ft=python sts=4 sw=4 ts=4
