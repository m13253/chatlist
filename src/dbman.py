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
        self.execute = self.db.execute
        self.commit = self.db.commit

    def create(self):
        self.db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                jid TEXT PRIMARY KEY UNIQUE,
                subscription TEXT DEFAULT 'none',
                isadmin INTEGER DEFAULT 0,
                isroot INTEGER DEFAULT 0,
                mute_until REAL DEFAULT 0.0,
                stop_until REAL DEFAULT 0.0
            );
            INSERT OR REPLACE INTO users (
                jid, subscription, isadmin, isroot
            ) VALUES (
                '', 'both', 1, 1
            );
        ''')
        self.db.commit()

    def update_root(self):
        self.db.execute("UPDATE users SET isroot=0 WHERE jid<>'';")
        if len(config.root):
            self.db.execute('UPDATE users SET isroot=1 WHERE jid IN (%s)' % ', '.join(("'"+str(i).replace("'", "''")+"'" for i in config.root)))
        self.db.commit()

    def update_subscription(self, subscriptions):
        subscriptions = dict(subscriptions)
        for i in subscriptions:
            if subscriptions[i]!='none':
                self.db.execute('''
                    INSERT OR IGNORE INTO uesrs (jid) VALUES (?);
                    UPDATE users SET subscription=? WHERE jid=?;
                ''', (str(i), str(subscriptions[i]), str(i)))
        self.db.execute("REMOVE FROM users WHERE subscription='none';")
        self.db.commit()

    def close(self):
        if self.db:
            self.db.close()
        self.db = None

    def __del__(self):
        self.close()

db = DBMan()

# vim: et ft=python sts=4 sw=4 ts=4
