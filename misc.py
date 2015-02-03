#!/usr/bin/env python

import errno
import gettext
import locale
import os
import pickle
import sleekxmpp
import sys
import time
import re

import config

gettext.install('messages', 'locale')
locale.setlocale(locale.LC_TIME, '')

lctime = lambda t: time.strftime('%c %Z', time.localtime(t))

restarting = False
quiting = False
msg_log = []
cmd_log = []
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
    nick=str(nick)
    return bool(nick and (nick[0] not in config.command_prefix) and (nick[0]!='-') and ('@' not in nick) and ('?' not in nick) and ('*' not in nick) and (nick.lower()!='root') and (nick.lower()!='admin') and (nick.lower()!='administrator') and (nick!='新昵称'))

def isjidvalid(jid):
    jid=str(jid)
    return bool(jid and 0<jid.find('@')<len(jid)-1)

def replace_prefix(s, prefix):
    res=''
    lastisslash=False
    for i in s:
        if lastisslash:
            if i=='-':
                res+=prefix
            else:
                res+=i
            lastisslash=False
        elif i=='/':
            lastisslash=True
        else:
            res+=i
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
    return '^'+res+'$'

def replace_globs_to_regex(glob):
    if isinstance(glob, str):
        return replace_glob_to_regex(glob)
    if len(glob)>0:
        return '^('+'|'.join([replace_glob_to_regex(i)[1:-1] for i in glob])+')$'
    else:
        return '^.*'

def find_users(xmpp, glob, isAdmin):
    haveglob=False
    regex=[]
    for i in glob:
        if not i or i.startswith('-'):
            continue
        regex.append(i)
        if '?' in i or '*' in i:
            haveglob=True
            break
    regex=re.compile(replace_globs_to_regex(glob))
    res=[]
    for i in xmpp.client_roster:
        if xmpp.client_roster[i]['to'] and xmpp.client_roster[i]['subscription']=='both':
            if isAdmin or not haveglob:
                if regex.match(i) or regex.match(getnick(xmpp, i)):
                    res.append(i)
            else:
                if regex.match(getnick(xmpp, i)):
                    res.append(i)
    res.sort()
    return res

data = {}

def load_data(filename=config.datafile):
    global data
    try:
        f=open(filename, 'rb')
        try:
            data=pickle.load(f)
        except (pickler.PickleError, ValueError):
            sys.stderr.write('Error when loading profile. Created an empty one.\n')
        finally:
            f.close()
    except IOError as e:
        if e.errno==errno.ENOENT:
            sys.stderr.write('Created an empty profile.\n')
        else:
            raise

def save_data(filename=config.datafile):
    save_okay=False
    f=open(filename+'~', 'wb')
    try:
        pickle.dump(data, f)
        save_okay=True
    finally:
        f.close()
    if save_okay:
        os.rename(filename+'~', filename)

time_unit={'u': .000001, 'U': .000001, 'z': .001, 'Z': .001, 'S': 1, 's': 1, 'm': 60, 'H': 3600, 'h': 3600, 'D': 86400, 'd': 86400, 'M': 2629743.7710168, 'Y': 31556925.2522016, 'y': 31556925.2522016, 'C': 31556925252.2016, 'c': 31556925252.2016}
time_unit_chars='cyMdhms'
class TimeUnit(float):
    def __new__(cls, s):
        s=str(s)
        if not s:
            raise ValueError
        if s[0]=='-':
            isNeg=True
            s=s[1:]
        elif s[0]=='+':
            isNeg=False
            s=s[1:]
        else:
            isNeg=False
        res=0
        cur=''
        for i in s:
            if i.isdigit() or i=='.':
                cur+=i
            elif i in time_unit:
                res+=float(cur)*time_unit[i]
                cur=''
            elif not i.isspace():
                raise ValueError('invalid liternal for %s(): %s' % (cls, repr(s)))
        if cur:
            res+=float(cur)
        if isNeg:
            res=-res
        return float.__new__(cls, res)
    def __repr__(self):
        return '%s(%s)' % (type(self).__name__, repr(str(self)))
    def __str__(self):
        value=float(self)
        if value<0:
            res='-'
            value=-value
        else:
            res=''
        for i in time_unit_chars[:-1]:
            if value>=time_unit[i]:
                times, value=divmod(value, time_unit[i])
                times=int(times)
                if times>0:
                    res+=str(times)+i
        i=time_unit_chars[-1]
        if value+value>=time_unit[i]:
            times, value=divmod(value, time_unit[i])
            times=int(times)
            if value+value>=time_unit[i]:
                times+=1
            if times>0:
                res+=str(times)+i
        if not res or res=='-':
            res='0'
        return res

def compare_status(a, b):
    if not a or a=='available':
        va=4
    elif a=='chat':
        va=5
    elif a=='dnd' or a=='busy':
        va=3
    elif a=='away':
        va=2
    elif a=='xa' or a=='extended away':
        va=1
    elif a=='unavailable':
        va=0
    else:
        va=6
    if not b or b=='available':
        vb=4
    elif b=='chat':
        vb=5
    elif b=='dnd' or b=='busy':
        vb=3
    elif b=='away':
        vb=2
    elif b=='xa' or b=='extended away':
        vb=1
    elif b=='unavailable':
        vb=0
    else:
        vb=6
    return va-vb

def get_status_name(s):
    if not s or s=='available':
        return _('available')
    elif s=='chat':
        return _('want chat')
    elif s=='dnd' or s=='busy':
        return _('do not disturb')
    elif s=='away':
        return _('away')
    elif s=='xa' or s=='extended away':
        return _('extended away')
    elif s=='unavailable':
        return _('unavailable')
    else:
        return s

def check_time(xmpp, from_dict, to_jid):
    if to_jid in from_dict:
        if from_dict[to_jid]==None:
            return False
        else:
            if from_dict[to_jid]>time.time():
                return False
            else:
                del from_dict[to_jid]
                save_data()
                try:
                    if to_jid not in data['stop'] and to_jid not in data['quiet']:
                        xmpp.send_presence(pto=to_jid, pshow='', pstatus=config.group_topic)
                except:
                    pass
                return True
    else:
        return True

# vim: et ft=python sts=4 sw=4 ts=4
