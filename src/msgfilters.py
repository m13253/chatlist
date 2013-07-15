#!/usr/bin/env python
# -*- coding: utf-8 -*-

import gettext
import re

import config
import misc


gettext.install('messages', 'locale')

re_autoreply = re.compile('[aA]uto ?[rR]eply[:：\\]]|自动回复[:：\\]]|我(现在)?有事情?不在|IM\\+|music\ messaging\ session|音乐信使会话|再和[您你]联系|<ding>')
re_ayt = re.compile('.{,5}([aA]ny ?(body|one) there|这?群?里?[边面]?有人在?[吗么马]).{,5}$')


def filter_autoreply(xmpp, msg):
    if re_autoreply.search(msg['body']):
        msg.reply(misc.replace_prefix(_('It seems that you are using auto reply or a plugin that automatically sends messages, please disable this function in order not to disturb other users in this group.\nIf you are sure that previous message is sent by you, please put /-say before your message and send your previous message again.\nThe last message you sent is:\n%s') % msg['body'], config.command_prefix[0])).send()
        return False
    return True


def filter_pastebin(xmpp, msg):
    if len(msg['body']) > 280:
        msg.reply(_('Your message is too long, please consider using a pastebin.')).send()
        return False
    return True


def filter_ayt(xmpp, msg):
    if re_ayt.match(msg['body']):
        msg.reply(misc.replace_prefix(_('Please type /-ls to list online users, or type /-help for further help.'), config.command_prefix[0])).send()
    return True


msg_filters = [filter_autoreply, filter_pastebin, filter_ayt]

# vim: et ft=python sts=4 sw=4 ts=4
