#!/usr/bin/env python

import gettext
import locale

import sleekxmpp

import config
import misc
import termcon
import utils

gettext.install('messages', 'locale')


class XMPPBot(sleekxmpp.ClientXMPP):

    def __init_(self, jid, password):
        super().__init__(jid, password)
        self.add_event_handler('session_start', self.sessionstart)
        self.add_event_handler('message', self.message)
        self.add_event_handler('presence_subscribe', self.subscribe)
        self.add_event_handler('presence_subscribed', self.subscribed)
        self.add_event_handler('presence_unsubscribe', self.unsubscribe)
        self.add_event_handler('got_online', self.gotonline)

    def sessionstart(self, event):
        termcon.writeln('Connected.')
        self.auto_authorize = True
        self.auto_subscribe = True
        self.get_roster()
        self.send_presence()

    @utils.prerr
    def subscribe(self, presence):
        raise NotImplementedError()

    @utils.prerr
    def subscribed(self, presence):
        raise NotImplementedError()

    @utils.prerr
    def unsubscribe(self, presence):
        raise NotImplementedError()

    @utils.prerr
    def gotonline(self, presence):
        raise NotImplementedError()

    @utils.prerr
    def message(self, msg):
        if misc.quiting:
            return
        if msg['type'] not in ('chat', 'normal'):
            return
        from_jid = msg['from']
        from_jid_bare = from_jid.bare
        msg_text = msg['body']
        msg_html = msg['html']
        termcon.writeln(repr((from_jid, msg_text, sleekxmpp.xmlstream.tostring(msg_html))))
        raise NotImplementedError()


@utils.prerr
def start():
    global xmpp
    try:
        xmpp = XMPPBot(config.JID, config.password)
        xmpp.register_plugin('xep_0030')  # Service Discovery
        xmpp.register_plugin('xep_0004')  # Data Forms
        xmpp.register_plugin('xep_0060')  # PubSub
        xmpp.register_plugin('xep_0199')  # XMPP Ping
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


# vim: et ft=python sts=4 sw=4 ts=4
