#!/usr/bin/env python

import gettext
import locale
import sys
import threading
import time

import config


gettext.install('messages', 'locale')
locale.setlocale(locale.LC_TIME, '')


class ConsoleThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.stdout_is_tty = sys.stdout.isatty()
        self.quiting = False

    def run(self):
        if self.stdout_is_tty:
            success = False
            while not self.quiting:
                sys.stderr.write('> ')
                try:
                    cmd = input()
                    success = True
                    print(cmd)
                except EOFError:
                    if success:
                        success = False
                        sys.stderr.write('\n')
                    else:
                        self.stop()

    def writeln(self, s):
        if self.stdout_is_tty and not self.quiting:
            sys.stderr.write('\r \r')
        for line in str(s).splitlines(True):
            sys.stdout.write(line)
        sys.stdout.write('\n')
        if self.stdout_is_tty and not self.quiting:
            sys.stderr.write('> ')

    def stop(self):
        sys.stderr.write('\r \r\n')
        self.quiting = True

    def __del__(self):
        self.quiting = True

console_thread = ConsoleThread()

# vim: et ft=python sts=4 sw=4 ts=4
