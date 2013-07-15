#!/usr/bin/env python

import gettext
import os
import random
import sleekxmpp
import sys
import time

import command
import config
import misc
import termcon

gettext.install('messages', 'locale')

if __name__=='__main__':
    misc.restarting = False
    misc.quiting = False
    termcon.console_thread.start()
    termcon.console_thread.join()
    exit()
    for i in ('stop', 'quiet', 'block'):
        if i not in misc.data:
            misc.data[i]={}
    if config.store_log:
        if 'msg_log' in misc.data:
            misc.msg_log=misc.data['msg_log']
        else:
            misc.data['msg_log']=misc.msg_log
        if 'cmd_log' in misc.data:
            misc.cmd_log=misc.data['cmd_log']
        else:
            misc.data['cmd_log']=misc.cmd_log
    for i in config.root:
        if i not in config.admins:
            config.admins.append(i)
    try:
        try:
            xmpp=XMPPBot(config.JID, config.password)
            xmpp.register_plugin('xep_0030') # Service Discovery
            xmpp.register_plugin('xep_0004') # Data Forms
            xmpp.register_plugin('xep_0060') # PubSub
            xmpp.register_plugin('xep_0199') # XMPP Ping
            if xmpp.connect(config.server):
                xmpp.process(block=True)
            else:
                sys.stderr.write('Connection error.')
                time.sleep(10)
                misc.restarting=True
        except Exception as e:
            sys.stderr.write('Exception: %s: %s\n' % (type(e).__name__, e))
            time.sleep(10)
            misc.restarting=True
        raise SystemExit
    except (SystemExit, KeyboardInterrupt):
        sys.stderr.write('Quiting...')
        time.sleep(3)
        xmpp.disconnect(wait=True)
        misc.save_data()
        sys.stderr.write('\n')
        if misc.restarting:
            sys.stderr.write('Restarting.\n')
            try:
                os.execlp('python3', 'python3', __file__)
            except:
                os.execlp('python', 'python', __file__)
        raise SystemExit

# vim: et ft=python sts=4 sw=4 ts=4
