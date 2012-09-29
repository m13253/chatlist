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
import msgfilters

gettext.install('messages', 'locale')

class XMPPBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('presence_subscribe', self.subscribe)
        self.add_event_handler('presence_subscribed', self.subscribed)
        self.add_event_handler('presence_unsubscribe', self.unsubscribe)
        self.add_event_handler('got_online', self.gotonline)

    def start(self, event):
        self.send_presence(pshow='', pnick=config.group_nick, pstatus=config.group_topic)
        self.get_roster()
        self.auto_authorize = True
        self.auto_subscribe = True
        sys.stderr.write('roster = [\n')
        for i in self.client_roster:
            if self.client_roster[i]['to']:
                if self.client_roster[i]['subscription']=='both':
                    sys.stderr.write('\t%s' % i)
                    misc.add_nicktable(self, i)
                    if not (misc.check_time(self, misc.data['stop'], i) or misc.check_time(self, misc.data['quiet'], i)):
                        self.send_presence(pto=i, pshow='dnd', pnick=config.group_nick, pstatus=config.group_topic)
                    sys.stderr.write('\n')
                elif self.client_roster[i]['subscription']=='to':
                    try:
                        misc.del_roster_item(i)
                        misc.client_roster.remove(i)
                        if i in misc.data['stop']:
                            del misc.data['stop'][i]
                    except:
                        pass
        sys.stderr.write(']\n')

    def gotonline(self, presence):
        try:
            from_jid=sleekxmpp.JID(presence['from']).bare
            if misc.check_time(self, misc.data['stop'], from_jid) and misc.check_time(self, misc.data['quiet'], from_jid):
                self.send_presence(pto=presence['from'], pshow='', pnick=config.group_nick, pstatus=config.group_topic)
            else:
                self.send_presence(pto=presence['from'], pshow='dnd', pnick=config.group_nick, pstatus=config.group_topic)
        except:
            pass

    def subscribe(self, presence):
        sys.stderr.write('%s subscribed me.\n' % presence['from'])
        self.send_presence(pto=jid, pshow='away', pnick=config.group_nick, pstatus=_('Not accepted subscription yet'))

    def subscribed(self, presence):
        jid=sleekxmpp.JID(presence['from']).bare
        sys.stderr.write('I subcribed %s.\n' % presence['from'])
        while True:
            to_nick=int(random.random()*90000+10000)
            if not misc.getnick(self, to_nick):
                break
            to_nick+=1
        to_nick='Guest'+str(to_nick)
        self.update_roster(jid, name=to_nick)
        misc.add_nicktable(self, jid)
        self.send_message(mto=presence['from'], mbody=misc.replace_prefix(config.welcome_message, config.command_prefix[0]), mtype='chat')
        self.send_message(mto=presence['from'], mbody=misc.replace_prefix(_('You have been given a random nickname %s, please use /-nick to change your nickname.'), config.command_prefix[0]) % to_nick, mtype='chat')
        self.send_message(mto=presence['from'], mbody=misc.replace_prefix(_('For more help, type /-help'), config.command_prefix[0]), mtype='chat')
        self.send_except(jid, _('%s has joined this group.') % to_nick)
        self.send_presence(pto=jid, pshow='', pnick=config.group_nick, pstatus=config.group_topic)

    def unsubscribe(self, presence):
        from_jid=sleekxmpp.JID(presence['from']).bare
        if from_jid in misc.data['stop'][from_jid]:
            del misc.data['stop'][from_jid]
            misc.save_data()
        from_nick=misc.getnick(self, from_jid)
        try:
            self.del_roster_item(from_jid)
            self.client_roster.remove(from_jid)
        except:
            pass
        sys.stderr.write('%s unsubscribed me.\n' % presence['from'])
        self.send_except(from_jid, _('%s has quited this group.') % from_nick)

    def message(self, msg):
        try:
            if misc.quiting:
                return
            if msg['type'] not in ('chat', 'normal'):
                return
            from_jid=msg['from'].bare
            body=msg['body']
            if not body:
                return
            sys.stderr.write('%s:\t%s\n' % (from_jid, body))
            if from_jid not in self.client_roster or self.client_roster[from_jid]['subscription']!='both':
                if self.client_roster[from_jid]['subscription']=='from':
                    msg.reply(_('You have not accept the buddy request.')).send()
                else:
                    msg.reply(_('You have not joined this group.')).send()
                return
            if len(body)>1 and body[0] in config.command_prefix and len(body.split(None, 1)[0])>1 and not (body[0]=='-' and body[1:].isdigit()):
                command.trigger(self, msg)
            else:
                presence_needs_update=False
                if from_jid in misc.data['stop']:
                    del misc.data['stop'][from_jid]
                    misc.save_data()
                    presence_needs_update=True
                if not misc.check_time(self, misc.data['quiet'], from_jid):
                    msg.reply(_('You have been quieted.')).send()
                    return
                if presence_needs_update:
                    self.send_presence(pto=from_jid, pshow='', pnick=config.group_nick, pstatus=config.group_topic)
                for msg_filter in msgfilters.msg_filters:
                    if not msg_filter(self, msg):
                        return
                for l in body.splitlines():
                    self.dispatch_message(from_jid, l)
        except UnicodeError:
            pass
        except SystemExit:
            raise
        except Exception as e:
            sys.stderr.write('Exception: %s: %s\n' % (type(e).__name__, e))

    def dispatch_message(self, from_jid, body):
        if from_jid=='orzbot@erhandsome.org':
            self.send_except(from_jid, body)
        else:
            self.send_except(from_jid, '%s: %s' % (misc.getnick(self, from_jid), body))

    def send_except(self, except_jid, body):
        nowtime=time.time()
        misc.msg_log.append((nowtime, body))
        if len(misc.msg_log)>config.logsize:
            misc.msg_log[len(misc.msg_log)-config.logsize:]=[]
        for i in self.client_roster:
            if i!=except_jid and self.client_roster[i]['to'] and self.client_roster[i]['subscription']=='both' and self.client_roster[i].resources:
                misc.check_time(self, misc.data['quiet'], i)
                if misc.check_time(self, misc.data['stop'], i) and (i not in misc.data['block'] or except_jid not in misc.data['block'][i]):
                    try:
                        self.send_message(mto=i, mbody=body, mtype='chat')
                    except:
                        pass

if __name__=='__main__':
    misc.restarting=False
    misc.quiting=False
    misc.load_data()
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
