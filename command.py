#!/usr/bin/env python

import gettext
import sleekxmpp
import sys

import config
import misc

gettext.install('messages', 'locale')

def trigger(xmpp, msg):
    try:
        from_jid=msg['from'].bare
        cmd=msg['body'][1:].split()
        prefix=msg['body'][0]
        if not cmd:
            return
        if cmd[0]=='quit':
            msg.reply(_('You have quited from this group.')).send()
            to_nick=misc.getnick(xmpp, from_jid)
            misc.del_nicktable(xmpp, from_jid)
            try:
                xmpp.del_roster_item(from_jid)
                xmpp.client_roster.remove(from_jid)
            except:
                pass
            xmpp.send_except(_('%s has quited from this group.') % to_nick)
        elif cmd[0]=='ping':
            msg.reply('Pong!').send()
        elif cmd[0]=='shutdown':
            if from_jid in config.admins:
                quiet=False
                for i in cmd[1:]:
                    if i.startswith('-'):
                        if 'r' in i:
                            misc.restarting=True
                        if 'q' in i:
                            quiet=True
                if misc.restarting:
                    msg.reply(_('Restarting.')).send(now=True)
                    if not quiet:
                        xmpp.send_except(from_jid, _('Restarting by %s.') % misc.getnick(xmpp, from_jid))
                else:
                    msg.reply(_('Shutting down.')).send(now=True)
                    if not quiet:
                        xmpp.send_except(from_jid, _('Shutting down by %s.') % misc.getnick(xmpp, from_jid))
                raise SystemExit
            else:
                msg.reply(_('Error: Permission denied.')).send()
        elif cmd[0]=='kick':
            if from_jid in config.admins:
                for i in cmd[1:]:
                    to_jid=misc.getjid(xmpp, i)
                    if to_jid:
                        sys.stderr.write('Kicking %s' % to_jid)
                        xmpp.send_message(mto=to_jid, mbody=_('You have been kicked by %s.') % misc.getnick(xmpp, from_jid), mtype='chat')
                        to_nick = misc.getnick(xmpp, to_jid)
                        misc.del_nicktable(xmpp, to_jid)
                        try:
                            xmpp.del_roster_item(to_jid)
                            xmpp.client_roster.remove(to_jid)
                        except:
                            pass
                        xmpp.send_except(to_jid, _('%s has been kicked by %s.') % (to_nick, misc.getnick(xmpp, from_jid)))
                        sys.stderr.write('\n')
                    else:
                        msg.reply(_('Error: User %s is not a member of this group.') % (cmd[1])).send()
            else:
                msg.reply(_('Error: Permission denied.')).send()
        elif cmd[0]=='nick':
            if len(cmd)==1:
                msg.reply(_('Your current nickname is %s.') % misc.getnick(xmpp, from_jid)).send()
            elif len(cmd)>=2:
                new_nick=cmd[1]
                for i in cmd[2:]:
                    new_nick+=i
                if not misc.isnickvalid(new_nick):
                    msg.reply(_('Nickname %s not vaild.') % new_nick).send()
                elif misc.getnick(xmpp, new_nick):
                    msg.reply(_('Nickname %s is already in use.') % new_nick).send()
                else:
                    oldnick=misc.getnick(xmpp, from_jid)
                    misc.change_nicktable(xmpp, from_jid, new_nick)
                    xmpp.update_roster(from_jid, name=new_nick)
                    xmpp.send_except(None, _('%s changed its nick to %s') % (oldnick, new_nick))
            else:
                msg.reply(misc.replace_prefix(_('Error: /-nick takes exactly one argument.'), prefix)).send()
        elif cmd[0]=='setnick':
            if from_jid in config.admins:
                if len(cmd)==3:
                    to_jid=misc.getjid(xmpp, cmd[1])
                    if to_jid:
                        if not misc.isnickvalid(new_nick):
                            msg.reply(_('Nickname %s not vaild.') % new_nick).send()
                        elif misc.getnick(xmpp, cmd[2]):
                            msg.reply(_('Nickname %s is already in use.') % cmd[2]).send()
                        else:
                            oldnick=misc.getnick(xmpp, cmd[1])
                            misc.change_nicktable(xmpp, from_jid, cmd[2])
                            xmpp.update_roster(cmd[1], name=cmd[2])
                            xmpp.send_except(None, _('%s is forced to changed its nick to %s.') % (oldnick, cmd[2]))
                    else:
                        msg.reply(_('User %s is not a member of this group.') % (cmd[1])).send()
                else:
                    msg.reply(misc.replace_prefix(_('Error: /-setnick takes exactly two arguments.'), prefix)).send()
            else:
                msg.reply(_('Error: Permission denied.')).send()
        elif cmd[0]=='ls':
            isAdmin = from_jid in config.admins
            option_a = False
            for i in cmd[1:]:
                if i.startswith('-'):
                    if 'a' in i:
                        option_a = True
            s=''
            for i in xmpp.client_roster:
                if xmpp.client_roster[i]['to']:
                    if option_a or xmpp.client_roster[i].resources:
                        s+='\n%s' % misc.getnick(xmpp, i)
                        if isAdmin:
                            s+='\t(%s)' % i
            msg.reply(s).send()
        elif cmd[0]=='eval':
            if from_jid in config.admins:
                msg.reply(str(eval(msg['body'].split(None, 1)[1]))).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
        elif cmd[0]=='exec':
            if from_jid in config.admins:
                exec(msg['body'].split(None, 1)[1])
                msg.reply(_('Command executed.')).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
        else:
            msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
    except SystemExit:
        raise
    except Exception as e:
        try:
            msg.reply(_('An error occured: %s: %s') % (e.__class__.__name__, e)).send()
        except:
            pass

# vim: et ft=python sts=4 sw=4 ts=4
