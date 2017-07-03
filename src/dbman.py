#!/usr/bin/env python

import gettext
import locale
import sqlite3

import config

gettext.install('messages', 'locale')


class DBMan:

    def __init__(self):
        self.db = None

    def connect(self, filename=config.datafile):
        self.db = sqlite3.Connection(filename)
        self.cursor = self.db.cursor
        self.execute = self.db.execute
        self.commit = self.db.commit

    def create(self):
        cursor = self.db.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                jid TEXT PRIMARY KEY UNIQUE,
                nick TEXT,
                subscription TEXT DEFAULT 'none',
                isadmin INTEGER DEFAULT 0,
                isroot INTEGER DEFAULT 0,
                mute_until REAL DEFAULT 0.0,
                stop_until REAL DEFAULT 0.0
            );
        ''')
        cursor.execute('''
            INSERT OR REPLACE INTO users (
                jid, subscription, isadmin, isroot
            ) VALUES (
                '', 'both', 1, 1
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS logs (
                time REAL,
                iscmd INTEGER DEFAULT 0,
                msg_text TEXT,
                msg_html TEXT
            );
        ''')
        self.db.commit()

    def update_root(self):
        self.db.execute("UPDATE users SET isroot=0 WHERE jid<>'';")
        if len(config.root):
            self.db.execute('UPDATE users SET isroot=1 WHERE jid IN (%s)' % ', '.join(("'" + str(i).replace("'", "''") + "'" for i in config.root)))
        self.db.commit()

    def update_roster(self, users):
        users = dict(users)
        cursor = self.db.cursor()
        for i in users:
            if 'subscription' not in users[i] or users[i]['subscription'] != 'none':
                cursor.execute('INSERT OR IGNORE INTO uesrs (jid) VALUES (?);', (str(i),))
                if 'subscription' in users[i]:
                    cursor.execute('UPDATE users SET subscription=? WHERE jid=?;', (str(users[i]['subscription']), str(i)))
                if 'nick' in users[i]:
                    cursor.execute('UPDATE users SET nick=? WHERE jid=?;', (str(users[i]['nick']), str(i)))
        cursor.execute("REMOVE FROM users WHERE subscription='none';")
        self.db.commit()

    def update_subscription(self, jid, subscription):
        jid = str(jid)
        cursor = self.db.cursor()
        if subscription:
            if subscription != 'none':
                cursor.execute('UPDATE users SET subscription=? WHERE jid=?;', (jid, str(subscription)))
            else:
                cursor.execute('REMOVE FROM users WHERE jid=?;', (jid,))
        self.db.commit()

    def update_nick(self, jid, nick):
        jid = str(jid)
        cursor = self.db.cursor()
        if nick:
            if nick != 'none':
                cursor.execute('UPDATE users SET nick=? WHERE jid=?;', (jid, str(nick)))
            else:
                cursor.execute('REMOVE FROM users WHERE jid=?;', (jid,))
        self.db.commit()

    def clean_log(self, logsize=config.logsize, cmdlogsize=config.cmdlogsize):
        cursor = self.db.cursor()
        success = False
        if logsize:
            curlogsize = cursor.execute('SELECT COUNT(time) FROM logs WHERE iscmd=0;').fetchone[0]
            if curlogsize > logsize:
                cursor.execute('DELETE FROM logs WHERE time IN (SELECT time FROM logs WHERE iscmd=0 ORDER BY time DESC LIMIT ?) AND iscmd=0;', (curlogsize - logsize,))
                success = True
        if cmdlogsize:
            curcmdlogsize = cursor.execute('SELECT COUNT(time) FROM logs WHERE iscmd<>0;').fetchone[0]
            if curlogsize > cmdlogsize:
                cursor.execute('DELETE FROM logs WHERE time IN (SELECT time FROM logs WHERE iscmd<>0 ORDER BY time DESC LIMIT ?) AND iscmd<>0;', (curlogsize - cmdlogsize,))
                success = True
        if success:
            cursor.execute('VACUUM')
            self.db.commit()

    def close(self):
        if self.db:
            self.db.close()
        self.db = None

    def __del__(self):
        self.close()

db = DBMan()

# vim: et ft=python sts=4 sw=4 ts=4
