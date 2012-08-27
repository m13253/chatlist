#!/usr/bin/env python

import sleekxmpp

def getnick(xmpp, jid):
    if jid not in xmpp.client_roster:
        return '<not join>'
    nick=xmpp.client_roster[jid]['name']
    if nick:
        return nick
    else:
        return sleekxmpp.JID(jid).user

# vim: et ft=python sts=4 sw=4 ts=4
