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

gettext.install('messages', 'locale')


@utils.prerr
def start_xmpp():
    try:
        xmpp=XMPPBot(config.JID, config.password)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0004') # Data Forms
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0071') # XHTML-IM
        xmpp.register_plugin('xep_0199') # XMPP Ping
        if xmpp.connect(config.server):
            xmpp.process(block=True)
        else:
            misc.restarting = True
            try:
                raise ConnectionError
            except NameError:
                raise OSError('Connection Error')
    except Exception:
        misc.restarting = True
        raise


if __name__=='__main__':
    misc.restarting = False
    misc.quiting = False
    termcon.console.start()
    dbman.db.connect()
    dbman.db.create()
    dbman.db.update_root()
    try:
        startxmpp()
        raise SystemExit
    except (SystemExit, KeyboardInterrupt):
        termcon.writeln('Quiting...')
        self.quiting = True
        time.sleep(3)
        xmpp.disconnect(wait=True)
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
