#!/usr/bin/env python

import sleekxmpp
import sys

import command
import config

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

    def subscribe(self, presence):
        sys.stderr.write('%s subscribed me.\n' % presence['from'])

    def subscribed(self, presence):
        sys.stderr.write('I subcribed %s.\n' % presence['from'])
        self.send_message(mto=presence['from'], mbody=config.welcome_message, mtype='chat')

    def unsubscribe(self, presence):
        self.client_roster.unsubscribe(presence['from'].bare)
        sys.stderr.write('%s unsubscribed me.\n' % presence['from'])

    def message(self, msg):
        try:
            if msg['type'] not in ('chat', 'normal'):
                return
            from_jid=msg['from'].bare
            body=msg['body']
            if not body:
                return
            sys.stderr.write('%s: %s\n' % (from_jid, body))
            if from_jid not in self.client_roster or self.client_roster[from_jid]['subscription']!='both':
                msg.reply('You have not subscribed to this group.').send()
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
            sys.stderr.write('Exception: %s\n' % e)

    def dispatch_message(self, from_jid, body):
        nick=self.client_roster[from_jid]['name']
        if not nick:
            nick=sleekxmpp.JID(from_jid).user
        for i in self.client_roster:
            if i==from_jid:
                continue
            if self.client_roster[i]['to'] and self.client_roster[i]['subscription']=='both':
                sys.stderr.write('Sending to %s.' % i)
                self.send_message(mto=i, mbody='%s: %s' % (nick, body), mtype='chat')
                sys.stderr.write('\n')

if __name__=='__main__':
    try:
        xmpp=XMPPBot(config.JID, config.password)
        xmpp.register_plugin('xep_0030') # Service Discovery
        xmpp.register_plugin('xep_0004') # Data Forms
        xmpp.register_plugin('xep_0060') # PubSub
        xmpp.register_plugin('xep_0199') # XMPP Ping
        if xmpp.connect():
            xmpp.process(block=True)
    except KeyboardInterrupt:
        sys.stderr.write('Quiting...')
        xmpp.disconnect(wait=True)
        sys.stderr.write('\n')
    except UnicodeEncodeError:
        pass
    except SystemExit:
        raise
    except Exception as e:
        sys.stderr.write('Exception: %s\n' %s)

# vim: et ft=python sts=4 sw=4 ts=4
