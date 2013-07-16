#!/usr/bin/env python

import gettext
import locale

import sleekxmpp

import config
import misc
import termcon
import utils

gettext.install('messages', 'locale')

class XMPPBot(sleekxmpp.clientXMPP):
    def __init_(self, jid, password):
        super().__init__(jid, password)
        self.add_event_handler('session_start', self.session_start)
        self.add_event_handler('message', self.message)
        self.add_event_handler('presence_subscribe', self.subscribe)
        self.add_event_handler('presence_subscribed', self.subscribed)
        self.add_event_handler('presence_unsubscribe', self.unsubscribe)
        self.add_event_handler('got_online', self.gotonline)

    def session_start(self, event):
        self.get_roster()
        self.auto_authorize = True
        self.auto_subscribe = True

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


# vim: et ft=python sts=4 sw=4 ts=4
