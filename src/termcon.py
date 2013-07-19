#!/usr/bin/env python

import gettext
import locale
import sys
import threading
import time
import traceback

import config
import utils
import misc
import xmppmain

gettext.install('messages', 'locale')


class ConsoleThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True
        self.quiting = False
        self.stdout_is_tty = sys.stdout.isatty()

    def run(self):
        if self.stdout_is_tty:
            success = False
            sys.stderr.write('> ')
            while not self.quiting:
                try:
                    cmd = input()
                    success = True
                    self.cmdprocess(cmd)
                except EOFError:
                    if success:
                        success = False
                        sys.stderr.write('\n')
                    else:
                        self.stop()
                if misc.quiting:
                    self.quiting = misc.quiting

    def writeln(self, s=''):
        if self.stdout_is_tty and not self.quiting:
            sys.stderr.write('\r \r')
        for line in str(s).splitlines(True):
            sys.stdout.write(line)
        sys.stdout.write('\n')
        if self.stdout_is_tty and not self.quiting:
            sys.stderr.write('> ')

    # Not planning to use logging module since it messes up whith '> ' prmopts.
    def printerr(self):
        try:
            e = sys.exc_info()
            self.writeln(''.join(traceback.format_exception(e[0], e[1], e[2])))
        except Exception:
            pass

    @utils.prerr
    def cmdprocess(self, cmd):
        writeln(eval(cmd))

    def stop(self):
        sys.stderr.write('\r \r\n')
        self.quiting = True

    def __del__(self):
        self.quiting = True


console = ConsoleThread()
start = console.start
writeln = console.writeln
printerr = console.printerr
stop = console.stop


# vim: et ft=python sts=4 sw=4 ts=4
