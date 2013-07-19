#!/usr/bin/env python

import gettext
import os
import random
import sleekxmpp
import sys
import time

import command
import config
import dbman
import misc
import termcon
import utils
import xmppmain

gettext.install('messages', 'locale')


if __name__ == '__main__':
    misc.restarting = False
    misc.quiting = False
    termcon.start()
    dbman.db.connect()
    dbman.db.create()
    dbman.db.update_root()
    try:
        xmppmain.start()
        raise SystemExit
    except (SystemExit, KeyboardInterrupt):
        termcon.writeln('Quiting...')
        misc.quiting = True
        time.sleep(3)
        try:
            xmppmain.xmpp.disconnect(wait=True)
        except Exception:
            pass
        sys.stderr.write('\n')
        if misc.restarting:
            time.sleep(10)
            termcon.writeln('Restarting.\n')
            try:
                os.execlp('python3', 'python3', __file__)
            except:
                os.execlp('python', 'python', __file__)
        raise SystemExit

# vim: et ft=python sts=4 sw=4 ts=4
