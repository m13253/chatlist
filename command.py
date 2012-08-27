#!/usr/bin/env python

import sleekxmpp
import sys

import config

def trigger(xmpp, msg):
    from_jid=msg['from'].bare
    cmd=msg['body'][1:].split()
    if not cmd:
        return
    if cmd[0]=='quit':
        xmpp.del_roster_item(from_jid)
    elif cmd[0]=='ping':
        msg.reply('Pong!').send()
    elif cmd[0]=='shutdown':
        if from_jid in config.admins:
            msg.reply('Shutting down.').send()
            raise SystemExit
        else:
            msg.reply('Permission denied.').send()
    elif cmd[0]=='ls':
        s=''
        for i in xmpp.client_roster:
            s+=i+'\n'
        msg.reply(s[:-1]).send()
    else:
        msg.reply('Unknown command.').send()

# vim: et ft=python sts=4 sw=4 ts=4
