#!/usr/bin/env python

import sleekxmpp
import sys

import config
import misc

def trigger(xmpp, msg):
    try:
        from_jid=msg['from'].bare
        cmd=msg['body'][1:].split()
        if not cmd:
            return
        if cmd[0]=='quit':
            msg.reply('You have quited from this group.').send()
            xmpp.del_roster_item(from_jid)
        elif cmd[0]=='ping':
            msg.reply('Pong!').send()
        elif cmd[0]=='shutdown':
            if from_jid in config.admins:
                msg.reply('Shutting down.').send(now=True)
                raise SystemExit
            else:
                msg.reply('Permission denied.').send()
        elif cmd[0]=='kick':
            if from_jid in config.admins:
                for i in cmd[1:]:
                    if i in xmpp.client_roster:
                        xmpp.send_message(mto=i, mbody='You have been kicked by %s.' % misc.getnick(xmpp, from_jid), mtype='chat')
                        xmpp.del_roster_item(i)
                        xmpp.send_except(i, '%s has been kicked by %s.' % (misc.getnick(xmpp, i), misc.getnick(xmpp, from_jid)))
                    else:
                        msg.reply('User %s is not a member of this group.' % (cmd[1])).send()
            else:
                msg.reply('Permission denied.').send()
        elif cmd[0]=='nick':
            if len(cmd)==1:
                msg.reply('Your current nickname is %s.' % misc.getnick(xmpp, from_jid))
            elif len(cmd)==2:
                oldnick=xmpp.client_roster[from_jid]['name']
                xmpp.update_roster(from_jid, name=cmd[1])
                xmpp.send_except(None, '%s changed its nick to %s' % (oldnick, cmd[1]))
            else:
                msg.reply('nick takes exactly one argument.').send()
        elif cmd[0]=='setnick':
            if from_jid in config.admins:
                if len(cmd)==3:
                    if cmd[1] in xmpp.client_roster:
                        oldnick=misc.getnick(xmpp, cmd[1])
                        xmpp.update_roster(cmd[1], name=cmd[2])
                        xmpp.send_except(None, '%s is forced to changed its nick to %s.' % (oldnick, cmd[2]))
                    else:
                        msg.reply('User %s is not a member of this group.' % (cmd[1])).send()
                else:
                    msg.reply('setnick takes exactly two arguments.').send()
            else:
                msg.reply('Permission denied.').send()
        elif cmd[0]=='ls':
            isAdmin = from_jid in config.admins
            s='\n'
            for i in xmpp.client_roster:
                if xmpp.client_roster[i]['to']:
                    s+='\n%s' % misc.getnick(xmpp, i)
                    if isAdmin:
                        s+='\t(%s)' % i
            msg.reply(s[1:]).send()
        else:
            msg.reply('Unknown command.').send()
    except SystemExit:
        raise
    except Exception as e:
        try:
            msg.reply('An error occured: %s' % e)
        except:
            pass

# vim: et ft=python sts=4 sw=4 ts=4
