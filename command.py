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
        cmd[0]=cmd[0].lower()
        prefix=msg['body'][0]
        if not cmd:
            return

        if cmd[0]=='eval':
            if from_jid in config.admins:
                msg.reply(str(eval(msg['body'].split(None, 1)[1]))).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
            return

        if cmd[0]=='exec':
            if from_jid in config.admins:
                exec(msg['body'].split(None, 1)[1])
                msg.reply(_('Command executed.')).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
            return

        if cmd[0]=='say':
            for l in msg['body'].split(None, 1)[1].splitlines():
                xmpp.dispatch_message(from_jid, l)
            return

        if cmd[0] in ('users', 'names', 'list', 'dir'):
            cmd[0]='ls'
            cmd.append('-a')
        elif cmd[0]=='online':
            cmd[0]='ls'
        elif cmd[0] in ('man', 'info'):
            cmd[0]='help'
        elif cmd[0] in ('stat', 'whowas', 'dig', 'nslookup'):
            cmd[0]='whois'
        elif cmd[0] in ('iam', 'whoami'):
            cmd=['whois', from_jid]
        elif cmd[0] in ('test', 'traceroute', 'tracert', 'pong'):
            cmd[0]='ping'
        elif cmd[0] in ('poweroff', 'halt', 'init0'):
            cmd[0]='shutdown'
        elif cmd[0] in ('restart', 'reboot', 'init6'):
            cmd=['shutdown', '-r']

        if cmd[0]=='help':
            if len(cmd)<2:
                cmd.append('main')
                if from_jid in config.admins:
                    cmd.append('admin')
            s=''
            for i in cmd[1:]:
                i=i.lstrip(prefix)
                if i.startswith('-'):
                    continue
                if i in help_msg:
                    s+='\n\n'+misc.replace_prefix(help_msg[i], prefix).strip('\n')
                elif ':'+i in help_msg:
                    s+='\n\n'+misc.replace_prefix(help_msg[':'+i], prefix).strip('\n')
            if len(s)>1:
                s=s[1:]
            else:
                s=_('Error: No help message for %s.' % cmd[1])
            msg.reply(s).send()
            return

        if not cmd[0].startswith(':') and cmd[0] in help_msg:
            for i in msg:
                if i=='--help':
                    msg.reply(misc.replace_prefix(help_msg[cmd[0]], prefix)).send()
                    return

        if cmd[0]=='init':
            if len(cmd)==2:
                if from_jid in config.admins:
                    xmpp.send_except(None, _('INIT: Switching to runlevel: %s') % cmd[1])
                else:
                    xmpp.send_message(mto=from_jid, mbody=_('INIT: Switching to runlevel: %s') % cmd[1], mtype='chat')
                if cmd[1]=='0':
                    cmd=['shutdown']
                elif cmd[1]=='6':
                    cmd=['shutdown', '-r']
                else:
                    return
            elif len(cmd)==1:
                msg.reply(misc.replace_prefix(_('Error: /-init must be run as PID 1.'), perfix)).send()
                return
            else:
                msg.reply(misc.replace_prefix(_('Error: /-init takes exactly one argument.'), perfix)).send()
                return

        if cmd[0]=='quit':
            msg.reply(_('You have quited this group.')).send()
            to_nick=misc.getnick(xmpp, from_jid)
            misc.del_nicktable(xmpp, from_jid)
            try:
                xmpp.del_roster_item(from_jid)
                xmpp.client_roster.remove(from_jid)
            except:
                pass
            xmpp.send_except(_('%s has quited this group.') % to_nick)
            return

        if cmd[0]=='ping':
            if len(cmd)>1:
                msg.reply('Pong: %s' % msg['body'].split(None, 1)[1]).send()
            else:
                msg.reply('Pong!').send()
            return

        if cmd[0]=='shutdown':
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
            return

        if cmd[0]=='kick':
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
            return

        if cmd[0]=='nick':
            if len(cmd)==1:
                msg.reply(_('Your current nickname is %s.') % misc.getnick(xmpp, from_jid)).send()
            elif len(cmd)>=2:
                new_nick=cmd[1]
                for i in cmd[2:]:
                    new_nick+=i.capitalize()
                if not misc.isnickvalid(new_nick):
                    msg.reply(_('Nickname %s not vaild.') % new_nick).send()
                elif misc.getnick(xmpp, new_nick):
                    msg.reply(_('Nickname %s is already in use.') % new_nick).send()
                else:
                    oldnick=misc.getnick(xmpp, from_jid)
                    misc.change_nicktable(xmpp, from_jid, new_nick)
                    xmpp.update_roster(from_jid, name=new_nick)
                    xmpp.send_except(None, _('%s changed its nick to %s.') % (oldnick, new_nick))
            else:
                msg.reply(misc.replace_prefix(_('Error: /-nick takes exactly one argument.'), prefix)).send()
            return

        if cmd[0]=='setnick':
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
                        msg.reply(_('Error: User %s is not a member of this group.') % (cmd[1])).send()
                else:
                    msg.reply(misc.replace_prefix(_('Error: /-setnick takes exactly two arguments.'), prefix)).send()
            else:
                msg.reply(_('Error: Permission denied.')).send()
            return

        if cmd[0]=='ls':
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
            return

        msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
    except SystemExit:
        raise
    except Exception as e:
        try:
            msg.reply(_('An error occured: %s: %s') % (e.__class__.__name__, e)).send()
        except:
            pass

help_msg = {
    ':all': '=:main',
    ':main': '=:common',
    ':common': _('''
Common commands:
\t/-ls\tList online users. Use /-ls -a for all users.
\t/-nick\tChange nickname or get current nickname.
\t/-say\tSend a message, usually a message starting with /-
\t/-whois\tGet personal information from the specific user.
\t/-ping\tTest whether you are still online.
\t/-quit\tQuit this group. Or just delete this group from your buddy list.
\t/-about\tSee information about the program powering this group -- chatlist.
For help of a specific command, type command name followed by /-help
'''),
    ':admin': _('''
Administrative commands:
\t/-kick\tKick someoue out of this group.
\t/-shutdown\tShutdown this group program. Use /-shutdown -r to restart.
\t/-setnick\tChange nickname of another user.
For more, use /-help danger
'''),
    ':danger': _('''
Danger zone:
\t/-eval\tEvaluate a Python command.
\t/-exec\tExecute a Python command.
\t/-system\tExecute a system command.
BE CAREFUL TO USE THESE COMMANDS!
'''),
# TODO: more help coming soon.
}

help_rescan_depth=100
while help_rescan_depth>0:
    help_rescan_depth-=1
    help_need_rescan=False
    for i in help_msg:
        if help_msg[i].startswith('='):
            dest=help_msg[i][1:]
            if dest in help_msg:
                if help_msg[dest].startswith('='):
                    help_need_rescan=True
                else:
                    help_msg[i]=help_msg[dest]
    if not help_need_rescan:
        del help_need_rescan
        break
else:
    sys.stderr.write('Error: Too many redirects in help contents.\n')
    raise RuntimeError

# vim: et ft=python sts=4 sw=4 ts=4
