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

gettext.install('messages', 'locale')

class XMPPBot(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('presence_subscribe', self.subscribe)
        self.add_event_handler('presence_subscribed', self.subscribed)
        self.add_event_handler('presence_unsubscribe', self.unsubscribe)

    def start(self, event):
        self.send_presence()
        self.get_roster()
        self.auto_authorize = True
        self.auto_subscribe = True
        sys.stderr.write('roster = [\n')
        for i in self.client_roster:
            if self.client_roster[i]['to']:
                sys.stderr.write('\t%s' % i)
                misc.add_nicktable(self, i)
                sys.stderr.write('\n')
        sys.stderr.write(']\n')

    def subscribe(self, presence):
        sys.stderr.write('%s subscribed me.\n' % presence['from'])

    def subscribed(self, presence):
        jid=sleekxmpp.JID(presence['from']).bare
        sys.stderr.write('I subcribed %s.\n' % presence['from'])
        while True:
            to_nick=int(random.random()*100000)
            if not misc.getnick(self, to_nick):
                break
            to_nick+=1
        to_nick='Guest'+str(to_nick)
        self.update_roster(jid, name=to_nick)
        misc.add_nicktable(self, jid)
        self.send_message(mto=presence['from'], mbody=config.welcome_message, mtype='chat')
        self.send_except(jid, _('%s has joined this group.') % to_nick)

    def unsubscribe(self, presence):
        from_jid=sleekxmpp.JID(presence['from']).bare
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
            if from_jid not in self.client_roster or self.client_roster[from_jid]['subscription']!='both':
                if self.client_roster[from_jid]['subscription']=='from':
                    msg.reply(_('You have not accept the buddy request.')).send()
                else:
                    msg.reply(_('You have not joined this group.')).send()
                return
            if len(body)>1 and body[0] in config.command_prefix:
                command.trigger(self, msg)
            else:
                for l in body.splitlines():
                    self.dispatch_message(from_jid, l)
        except UnicodeEncodeError:
            pass
        except SystemExit:
            raise
        except Exception as e:
            sys.stderr.write('Exception: %s: %s\n' % (type(e).__name__, e))

    def dispatch_message(self, from_jid, body):
        self.send_except(from_jid, '%s: %s' % (misc.getnick(self, from_jid), body))

    def send_except(self, except_jid, body):
        sys.stderr.write('%s: %s\n' % (except_jid, body))
        for i in self.client_roster:
            if i!=except_jid and self.client_roster[i]['to'] and self.client_roster[i]['subscription']=='both' and self.client_roster[i].resources:
                try:
                    sys.stderr.write('Sending to %s.' % i)
                    self.send_message(mto=i, mbody=body, mtype='chat')
                    sys.stderr.write('\n')
                except:
                    pass

if __name__=='__main__':
    misc.restarting=False
    try:
        xmpp=XMPPBot(config.JID, config.password)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0004') # Data Forms
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping
        if xmpp.connect():
            xmpp.process(block=True)
        else:
            sys.stderr.write('Connection error.')
            time.sleep(10)
            misc.restarting=True
        raise SystemExit
    except UnicodeEncodeError:
        pass
    except (SystemExit, KeyboardInterrupt):
        sys.stderr.write('Quiting...')
        xmpp.disconnect(wait=True)
        sys.stderr.write('\n')
        if misc.restarting:
            sys.stderr.write('Restarting.\n')
            try:
                os.execlp('python3', 'python3', __file__)
            except:
                os.execlp('python', 'python', __file__)
        raise SystemExit
    except Exception as e:
        sys.stderr.write('Exception: %s\n' %s)

# vim: et ft=python sts=4 sw=4 ts=4
