import sqlite3
from random import randint, choice
from datetime import datetime


class Database:
    def __init__(self, filename):
        self.conn = sqlite3.connect(filename)
        self.cur = self.conn.cursor()

        self.cur.execute("""
                         CREATE TABLE IF NOT EXISTS users
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         client_name TEXT NOT NULL,
                         log TEXT NOT NULL,
                         account TEXT NOT NULL,
                         currency TEXT NOT NULL,
                         datetime TEXT NOT NULL)
                         """)

        self.conn.commit()


    def add_entry(self, args, kwargs):
        print(args, kwargs)
        sql = """
            INSERT INTO users (client_name, log, account, currency, datetime)
            VALUES (?, ?, ?, ?, ?)
            """
        # self.cur.execute(sql, (client_name, log, account.get_name(), account.currency, datetime.now()))
        self.conn.commit()

    def show_table(self, **kwargs):
        if not kwargs:
            sql = "SELECT * FROM users"

        if 'name' in kwargs:
            sql = self.selection_by_names(kwargs['name'])

        if 'account' in kwargs:
            sql = self.selection_by_accounts(kwargs['account'])

        if 'date' in kwargs:
            sql = self.selection_by_dates(kwargs['dates'])

        self.cur.execute(sql)

        for line in self.cur.fetchall():
                print(*line)

    def selection_by_id(self, *args):
        placeholders = ','.join('?' for _ in args)
        return (f"SELECT * FROM users WHERE id IN ({placeholders})", args)
        
    def selection_by_names(self, *args):
        placeholders = ','.join('?' for _ in args)
        return (f"SELECT * FROM users WHERE client IN ({placeholders})", args)

    def selection_by_accounts(self, *args):
        placeholders = ','.join('?' for _ in args)
        return (f"SELECT * FROM users WHERE account IN ({placeholders})", args)

    def selection_by_currency(self, *args):
        placeholders = ','.join('?' for _ in args)
        return (f"SELECT * FROM users WHERE currency IN ({placeholders})", args)

    def selection_by_dates(self, *args):
        placeholders = ','.join('?' for _ in args)
        return (f"SELECT * FROM users WHERE datetime IN ({placeholders})", args)
    
    def delete_rows(self, **kwargs):
        if not kwargs:
            sql = "DELETE TABLE users"
        if 'date' in kwargs:
            sql = "DELETE FROM users WHERE datetime = ?, (kwargs['date'])"


# obj = Database()
# obj.show_table({'name': ('Игнатова Дарья', ), 'date': (datetime(2025, 4, 23), datetime(2025, 5, 23))})
# obj.show_table({'name': ('Иванов Иван', ), 'account': ('Invest_rub', 'Debit_rub')})
# obj.show_table({'currency': ('usd', )})
# obj.show_table({'account': ('Invest_rub', 'Debit_rub', 'Credit_rub'), 'date': (datetime(2025, 4, 1), datetime(2025, 5, 1))})
