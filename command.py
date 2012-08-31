#!/usr/bin/env python

import bisect
import gettext
import re
import sleekxmpp
import subprocess
import sys
import time

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

        if cmd[0] in ('users', 'user', 'names', 'name', 'list', 'dir', 'la'):
            cmd[0]='ls'
            cmd.append('-a')
        elif cmd[0]=='online':
            cmd[0]='ls'
        elif cmd[0]=='ll':
            cmd[0]='ls'
            cmd.append('-l')
        elif cmd[0] in ('lla', 'lal'):
            cmd[0]='ls'
            cmd.append('-la')
        elif cmd[0] in ('man', 'info'):
            cmd[0]='help'
        elif cmd[0] in ('stat', 'whowas', 'dig', 'nslookup'):
            cmd[0]='whois'
        elif cmd[0] in ('iam', 'whoami'):
            cmd=['whois', from_jid]
        elif cmd[0] in ('pm', 'dm', 'query', 'tell'):
            cmd[0]='msg'
        elif cmd[0] in ('test', 'traceroute', 'tracert', 'pong'):
            cmd[0]='ping'
        elif cmd[0] in ('poweroff', 'halt'):
            cmd[0]='shutdown'
        elif cmd[0] in ('restart', 'reboot'):
            cmd[0]='shutdown'
            cmd.append('-r')
        elif cmd[0] in ('rm', 'del', 'remove', 'delete'):
            cmd[0]='kick'
        elif cmd[0] in ('nickname', 'alias'):
            cmd[0]='nick'
        elif cmd[0] in ('mv', 'move', 'ren', 'rename'):
            cmd[0]='setnick'
        elif cmd[0]=='run':
            cmd[0]='system'
        elif cmd[0]=='quote':
            cmd[0]='say'
        elif cmd[0]=='action':
            cmd[0]='me'
        elif cmd[0] in ('pause', 'sleep', 'delay'):
            cmd[0]='stop'
        elif cmd[0]=='on':
            cmd=['stop', 'off']
        elif cmd[0]=='off':
            cmd=['stop', 'forever']
        elif cmd[0]=='log':
            cmd[0]='old'
        elif cmd[0]=='mute':
            cmd[0]='quiet'
        elif cmd[0] in ('part', 'leave', 'exit', 'bye'):
            cmd[0]='quit'
        elif cmd[0]=='about':
            cmd=['help', ':about']
        elif len(cmd[0])>4 and cmd[0].startswith('init'):
            cmd.insert(1, cmd[0][4:])
            cmd[0]='init'

        if cmd[0]=='say':
            if misc.check_time(misc.data['quiet'], from_jid):
                for l in msg['body'].split(None, 1)[1].splitlines():
                    xmpp.dispatch_message(from_jid, l)
            else:
                msg.reply(_('You have been quieted.')).send()
            return

        if cmd[0]=='me':
            if misc.check_time(misc.data['quiet'], from_jid):
                from_nick=misc.getnick(xmpp, from_jid)
                for l in msg['body'].split(None, 1)[1].splitlines():
                    xmpp.send_except(None, '* %s %s' % (from_nick, l))
            else:
                msg.reply(_('You have been quieted.')).send()
            return

        misc.cmd_log.append((time.time(), '%s: %s' % (from_jid, msg['body'])))
        if len(misc.cmd_log)>config.cmdlogsize:
            misc.cmd_log=misc.cmd_log[:-config.cmdlogsize]

        if cmd[0]=='eval':
            if from_jid in config.root:
                if len(cmd)>1:
                    msg.reply(str(eval(msg['body'].split(None, 1)[1]))).send()
                else:
                    msg.reply(misc.replace_prefix(_('Error: /-eval takes arguments'), prefix)).send()
            elif from_jid in config.admins:
                msg.reply(_('Error: Permission denied.')).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
            return

        if cmd[0]=='exec':
            if from_jid in config.root:
                if len(cmd)>1:
                    exec(msg['body'].split(None, 1)[1])
                    msg.reply(_('Command executed.')).send()
                else:
                    msg.reply(misc.replace_prefix(_('Error: /-exec takes arguments'), prefix)).send()
            elif from_jid in config.admins:
                msg.reply(_('Error: Permission denied.')).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
            return

        if cmd[0]=='system':
            if from_jid in config.root:
                if len(cmd)>1:
                    msg.reply('\n'+subprocess.getoutput(msg['body'].split(None, 1)[1])).send()
                else:
                    msg.reply(misc.replace_prefix(_('Error: /-system takes arguments'), prefix)).send()
            elif from_jid in config.admins:
                msg.reply(_('Error: Permission denied.')).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: Unknown command. For help, type /-help'), prefix)).send()
            return

        if cmd[0]=='msg':
            if len(cmd)>=2:
                to_jid=misc.getjid(xmpp, cmd[1])
                if to_jid:
                    xmpp.send_message(mto=to_jid, mbody='%s (%s): %s' % (misc.getnick(xmpp, from_jid), _('DM'), msg['body'].split(None, 2)[2]), mtype='chat')
                    msg.reply(_('Your message has been sent.'))
                else:
                    msg.reply(_('Error: User %s is not a member of this group.') % (cmd[1])).send()
            else:
                msg.reply(misc.replace_prefix(_('Error: /-setnick takes exactly two arguments.'), prefix)).send()
            return

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
                s=_('Error: No help message for %s.') % cmd[1]
            msg.reply(s).send()
            return

        if not cmd[0].startswith(':') and cmd[0] in help_msg:
            for i in cmd[1:]:
                if i=='--help':
                    msg.reply('\n'+misc.replace_prefix(help_msg[cmd[0]], prefix).strip('\n')).send()
                    return

        if cmd[0]=='init':
            if len(cmd)==2:
                if cmd[1] in ('S', 's'):
                    cmd[1]='single'
                if from_jid in config.admins:
                    xmpp.send_except(None, _('INIT: Switching to runlevel: %s') % cmd[1])
                else:
                    xmpp.send_message(mto=from_jid, mbody=_('INIT: Switching to runlevel: %s') % cmd[1], mtype='chat')
                if cmd[1]=='0':
                    cmd[0]='shutdown'
                    del cmd[1]
                elif cmd[1]=='6':
                    cmd[0]='shutdown'
                    cmd[1]='-r'
                else:
                    return
            elif len(cmd)==1:
                msg.reply(misc.replace_prefix(_('Error: /-init must be run as PID 1.'), prefix)).send()
                return
            else:
                msg.reply(misc.replace_prefix(_('Error: /-init takes exactly one argument.'), perfix)).send()
                return

        if cmd[0]=='quit':
            msg.reply(_('You have quited this group.')).send()
            if from_jid in misc.data['stop']:
                del misc.data['stop'][from_jid]
                misc.save_data()
            to_nick=misc.getnick(xmpp, from_jid)
            misc.del_nicktable(xmpp, from_jid)
            try:
                xmpp.del_roster_item(from_jid)
                xmpp.client_roster.remove(from_jid)
            except:
                pass
            xmpp.send_except(_('%s has quited this group.') % to_nick)
            return

        if cmd[0]=='old':
            from_log=misc.msg_log
            arg=[]
            for i in cmd[1:]:
                if i.startswith('-'):
                    if 'a' in i and from_jid in config.admins:
                        from_log=misc.cmd_log
                elif i:
                    arg.append(i)
            try:
                if len(arg)>=1:
                    from_time=arg[0]
                    if len(arg)>=2:
                        len_time=arg[1]
                    else:
                        len_time=from_time
                else:
                    from_time='25'
                    len_time=from_time
                if from_time.isdigit():
                    from_time=int(from_time)
                else:
                    from_time=misc.TimeUnit(from_time)
                if len_time.isdigit():
                    len_time=int(len_time)
                else:
                    len_time=misc.TimeUnit(len_time)
            except ValueError:
                msg.reply(_('Error: Invalid time specification.')).send()
                return
            res=[]
            nowtime=time.time()
            try:
                if isinstance(from_time, misc.TimeUnit):
                    res=from_log[bisect.bisect_left(from_log, (nowtime-from_time,)):]
                    if isinstance(len_time, misc.TimeUnit):
                        res=res[:bisect.bisect(res, (nowtime-from_time+len_time,))]
                    else:
                        res=res[:len_time]
                else:
                    res=from_log[-from_time:]
                    if isinstance(len_time, misc.TimeUnit):
                        res=res[:bisect.bisect(res, (res[0][0]+len_time,))]
                    else:
                        res=res[:len_time]
                res=res[:100]
            except IndexError:
                pass
                raise
            if res:
                sres=''
                sres+='\n'+_('Start:\t%s') % misc.lctime(res[0][0])
                for i in res:
                    sres+='\n(%s) %s' % (time.strftime("%T", time.localtime(i[0])), i[1])
                sres+='\n'+_('End:\t%s') % misc.lctime(res[-1][0])
                msg.reply(sres).send()
            else:
                msg.reply(_('No messages match your criteria.')).send()
            return

        if cmd[0]=='stop':
            if len(cmd)>1:
                to_time=''.join(cmd[1:])
                try:
                    if to_time in ('ever', 'forever'):
                        misc.data['stop'][from_jid]=None
                        misc.save_data()
                    elif to_time in ('off', 'never'):
                        if from_jid in misc.data['stop']:
                            del misc.data['stop'][from_jid]
                            misc.save_data()
                    else:
                        to_time=misc.TimeUnit(to_time)
                        if to_time>0:
                            to_time=time.time()+misc.TimeUnit(to_time)
                            misc.data['stop'][from_jid]=to_time
                        elif from_jid in misc.data['stop']:
                            del misc.data['stop'][from_jid]
                        misc.save_data()
                except ValueError:
                        msg.reply(_('Error: Invalid time specification.')).send()
                        return
            if from_jid in misc.data['stop']:
                to_time=misc.data['stop'][from_jid]
                if to_time==None:
                    msg.reply(_('You will never receive messages.')).send()
                else:
                    msg.reply(_('You will not receive messages until %s.') % misc.lctime(to_time)).send()
            else:
                msg.reply(_('You are currently receiving messages.')).send()
            return

        if cmd[0]=='ping':
            if len(cmd)>1:
                msg.reply('Pong: %s' % msg['body'].split(None, 1)[1]).send()
            else:
                msg.reply('Pong!').send()
            return

        if cmd[0]=='shutdown':
            if from_jid in config.admins:
                misc.quiting=True
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
                elif from_jid in config.root:
                    msg.reply(_('Shutting down.')).send(now=True)
                    if not quiet:
                        xmpp.send_except(from_jid, _('Shutting down by %s.') % misc.getnick(xmpp, from_jid))
                else:
                    msg.reply(_('Error: Permission denied.')).send()
                raise SystemExit
            else:
                msg.reply(_('Error: Permission denied.')).send()
            return

        if cmd[0]=='kick':
            if from_jid in config.admins:
                if len(cmd)<=1:
                    msg.reply(misc.replace_prefix(_('Error: /-kick takes at least one argument.'), prefix)).send()
                    return
                if len(cmd)>2:
                    reason=msg['body'].split(None, 2)[2]
                else:
                    reason=None
                success=False
                for to_jid in misc.find_users(xmpp, cmd[1], True):
                    success=True
                    sys.stderr.write('Kicking %s.' % to_jid)
                    if reason:
                        xmpp.send_message(mto=to_jid, mbody=_('You have been kicked by %s. (%s)') % (misc.getnick(xmpp, from_jid), reason), mtype='chat')
                    else:
                        xmpp.send_message(mto=to_jid, mbody=_('You have been kicked by %s.') % misc.getnick(xmpp, from_jid), mtype='chat')
                    if to_jid in misc.data['stop']:
                        del misc.data['stop'][to_jid]
                    to_nick = misc.getnick(xmpp, to_jid)
                    misc.del_nicktable(xmpp, to_jid)
                    try:
                        xmpp.del_roster_item(to_jid)
                        xmpp.client_roster.remove(to_jid)
                    except:
                        pass
                    if reason:
                        xmpp.send_except(to_jid, _('%s has been kicked by %s. (%s)') % (to_nick, misc.getnick(xmpp, from_jid), reason))
                    else:
                        xmpp.send_except(to_jid, _('%s has been kicked by %s.') % (to_nick, misc.getnick(xmpp, from_jid)))
                    sys.stderr.write('\n')
                if success:
                    misc.save_data()
                else:
                    msg.reply(_('Error: User %s is not a member of this group.') % (cmd[1])).send()
            else:
                msg.reply(_('Error: Permission denied.')).send()
            return

        if cmd[0]=='quiet':
            if from_jid in config.admins:
                if len(cmd)<=1:
                    msg.reply(misc.replace_prefix(_('Error: /-quiet takes at least one argument.'), prefix)).send()
                    return
                if len(cmd)>2:
                    to_time=''.join(cmd[2:])
                else:
                    to_time=None
                try:
                    if to_time in ('ever', 'forever', None):
                        to_time=None
                    elif to_time in ('off', 'never'):
                        to_time='off'
                    else:
                        to_time=misc.TimeUnit(to_time)
                        if to_time>0:
                            to_time=time.time()+misc.TimeUnit(to_time)
                        else:
                            to_time='off'
                except ValueError:
                        msg.reply(_('Error: Invalid time specification.')).send()
                        return
                success=False
                for to_jid in misc.find_users(xmpp, cmd[1], True):
                    success=True
                    sys.stderr.write('Quieting %s.' % to_jid)
                    if to_jid in misc.data['quiet']:
                        orig_time=misc.data['quiet'][to_jid]
                    else:
                        orig_time='off'
                    if to_time!='off':
                        misc.data['quiet'][to_jid]=to_time
                    else:
                        if to_jid in misc.data['quiet']:
                            del misc.data['quiet'][to_jid]
                    if orig_time==to_time:
                        continue
                    if to_time==None:
                        xmpp.send_message(mto=to_jid, mbody=_('You have been quieted by %s.') % misc.getnick(xmpp, from_jid), mtype='chat')
                    elif to_time=='off':
                        xmpp.send_message(mto=to_jid, mbody=_('You have been stopped quieting by %s.') % misc.getnick(xmpp, from_jid), mtype='chat')
                    else:
                        xmpp.send_message(mto=to_jid, mbody=_('You have been quieted by %s until %s.') % (misc.getnick(xmpp, from_jid), misc.lctime(to_time)), mtype='chat')
                    to_nick = misc.getnick(xmpp, to_jid)
                    if to_time==None:
                        xmpp.send_except(to_jid, _('%s has been quieted by %s.') % (to_nick, misc.getnick(xmpp, from_jid)))
                    elif to_time=='off':
                        xmpp.send_except(to_jid, _('%s has been stopped quieting by %s.') % (to_nick, misc.getnick(xmpp, from_jid)))
                    else:
                        xmpp.send_except(to_jid, _('%s has been quieted by %s until %s.') % (to_nick, misc.getnick(xmpp, from_jid), misc.lctime(to_time)))
                    sys.stderr.write('\n')
                if success:
                    misc.save_data()
                else:
                    msg.reply(_('Error: User %s is not a member of this group.') % (cmd[1])).send()
            else:
                msg.reply(_('Error: Permission denied.')).send()
            return

        if cmd[0]=='setnick':
            if len(cmd)==3:
                if from_jid in config.admins:
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
                    return
                elif misc.getjid(xmpp, cmd[1])==from_jid:
                    cmd[0]='nick'
                    del cmd[1]
                else:
                    msg.reply(_('Error: Permission denied.')).send()
                    return
            else:
                msg.reply(misc.replace_prefix(_('Error: /-setnick takes exactly two arguments.'), prefix)).send()
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

        if cmd[0]=='ls':
            isAdmin = from_jid in config.admins
            option_a = False
            option_l = False
            glob = []
            for i in cmd[1:]:
                if i.startswith('-'):
                    if 'a' in i:
                        option_a = True
                    if 'l' in i:
                        option_l = True
                else:
                    glob.append(i)
            s=''
            user_count=0
            for i in misc.find_users(xmpp, glob, isAdmin):
                to_resources=xmpp.client_roster[i].resources
                if option_a or to_resources:
                    user_count+=1
                    s+='\n\t%s' % misc.getnick(xmpp, i)
                    if option_l:
                        if not misc.check_time(misc.data['stop'], i):
                            s+='\t'+_('<Stopped>')
                        if to_resources:
                            to_priority=-1
                            to_show=''
                            to_status='unavailable'
                            for j in to_resources:
                                if to_resources[j]['priority']>to_priority or (to_resources[j]['priority']==to_priority and misc.compare_status(to_resources[j]['show'], to_status)>=0):
                                    to_priority=to_resources[j]['priority']
                                    to_show=to_resources[j]['show']
                                    to_status=to_resources[j]['status']
                            s+='\t(%s)' % misc.get_status_name(to_show)
                            if to_status:
                                s+=' [%s]' % to_status
                        else:
                            s+='\t(%s)' % _('unavailable')
                    else:
                        if isAdmin:
                            s+='\t(%s)' % i
            s+='\n'+(_('Total %d') % user_count)
            msg.reply(s).send()
            return

        if cmd[0]=='whois':
            isAdmin = from_jid in config.admins
            glob=[]
            for i in cmd[1:]:
                if not i.startswith('-'):
                    glob.append(i)
            if not glob:
                msg.reply(misc.replace_prefix(_('Error: /-whois takes at least one argument.'), prefix)).send()
                return
            s=''
            for i in misc.find_users(xmpp, glob, isAdmin):
                s+='\n\n'+_('Nickname:\t%s') % misc.getnick(xmpp, i)
                if isAdmin:
                    s+='\n'+_('Jabber ID:\t%s') % i
                else:
                    s+='\n'+_('Jabber ID:\t%s@%s') % ('*'*len(sleekxmpp.JID(i).user), sleekxmpp.JID(i).domain)
                if not misc.check_time(misc.data['stop'], i):
                    if misc.data['stop'][i]==None:
                        s+='\n'+_('Not receiving messages.')
                    else:
                        s+='\n'+_('Not receiving messages until %s.') % misc.lctime(misc.data['stop'][i])
                if not misc.check_time(misc.data['quiet'], i):
                    if misc.data['quiet'][i]==None:
                        s+='\n'+_('Quieted.')
                    else:
                        s+='\n'+_('Quieted until %s.') % misc.lctime(misc.data['quiet'][i])
                to_resources=xmpp.client_roster[i].resources
                if to_resources:
                    s+='\n'+_('Online resources:')
                    for j in to_resources:
                        s+='\n\t%s\t(%s)' % (j, misc.get_status_name(to_resources[j]['show']))
                        if to_resources[j]['status']:
                            s+='\t[%s]' % to_resources[j]['status']
            msg.reply(s[1:]).send()
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
    ':about': _('''
This group is powered by chatlist,
A XMPP chat program that bounces messages to all its subscribers.

Released under LGPL 3.0+

Visit project repository: https:////github.com//m13253//chatlist
'''),
    'about': _('''
See information about the program powering this group -- chatlist.

Usage: /-about
'''),
    'ls': _('''
List users, by default, list only online users.

Usage: /-ls [-a] [-l]
\t-a\tList all users instead of only online users.
\t-l\tShow user status.

Alias: /-la /-ll /-lla /-lal
'''), 'la': '=ls', 'll': '=ls', 'lla': '=ls', '=lal': '=ls',
    'nick': _('''
Change nickname or get current nickname.

Usage: /-nick <nickname>

Nickname must not contain these characters: @ ? *
Nickname starting with - is also unacceptable.

Alias: /-nickname /-alias
'''),
    'setnick': _('''
Change nickname of another user.

Usage: /-setnick <target> <nickname>

Alias: /-mv /-move /-ren /-rename
'''), 'mv': '=setnick', 'move': '=setnick', 'ren': '=setnick', 'rename': '=setnick',
    'shutdown': _('''
Shutdown this group program.

Usage: /-shutdown [-r] [-q]
\t-r\tRestart this program after shutting down.
\t-q\tQuiet mode. Do not broadcast message when shutting down.

Alias: /-halt /-restart /-poweroff /-reboot
'''), 'halt': '=shutdown', 'restart': '=shutdown', 'poweroff': '=shutdown', 'reboot': '=shutdown',
    'init': _('''
Process control initialization
INIT is the parent of all processes.

Usage: /-init [123456S]
'''), 'init0': '=init', 'init6': '=init',
    'help': _('''
See help contents of a specific command.

Usage: /-help <command>

Alias: /-man /-info
'''), 'man': '=help', 'info': '=help',
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
