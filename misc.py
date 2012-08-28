#!/usr/bin/env python

import sleekxmpp
import re

import config

restarting = False
quiting = False
nick_table = {}

def add_nicktable(xmpp, jid):
    nick_table[getnick(xmpp, jid)] = jid

def change_nicktable(xmpp, jid, newnick):
    oldnick = getnick(xmpp, jid)
    nick_table[newnick] = jid
    if oldnick in nick_table:
        del nick_table[oldnick]

def del_nicktable(xmpp, jid):
    nick = getnick(xmpp, jid)
    if nick in nick_table:
        del nick_table[nick]

def get_nicktable(xmpp, nick):
    if nick in nick_table:
        return nick_table[nick]
    else:
        return None

def getnick(xmpp, nick_or_jid):
    if nick_or_jid in nick_table:
        return nick_or_jid
    elif isjidvalid(nick_or_jid) and nick_or_jid in xmpp.client_roster and xmpp.client_roster[nick_or_jid]['to']:
        nick=xmpp.client_roster[nick_or_jid]['name']
        if nick:
            return nick
        else:
            return sleekxmpp.JID(nick_or_jid).user
    else:
        return None

def getjid(xmpp, nick_or_jid):
    if nick_or_jid in nick_table:
        return nick_table[nick_or_jid]
    elif isjidvalid(nick_or_jid) and nick_or_jid in xmpp.client_roster and xmpp.client_roster[nick_or_jid]['to']:
        return nick_or_jid
    else:
        return None

def isnickvalid(nick):
    return nick and (nick[0] not in config.command_prefix) and (nick[0]!='-') and ('@' not in nick) and ('?' not in nick) and ('*' not in nick) and (nick.lower()!='root') and (nick.lower()!='admin') and (nick.lower()!='administrator')

def isjidvalid(jid):
    return jid and 0<jid.find('@')<len(jid)-1

def replace_prefix(s, prefix):
    res=''
    lastisslash=False
    for i in prefix:
        if lastisslash:
            if i='-':
                res+=prefix
            else:
                res+=i
            lastisslash=False
        elif i=='/':
            lastisslash=True
        else:
            res+=prefix
    if lastisslash:
        res+='/'
    return res

def replace_glob_to_regex(glob):
    res=''
    for i in glob:
        if i=='*':
            res+='.*'
        elif i=='?':
            res+='.'
        else:
            res+=re.escape(i)
    return res

# vim: et ft=python sts=4 sw=4 ts=4
