import sqlite3
from random import randint, choice
from datetime import date


class Database:
    def __init__(self, filename='bank.db'):
        self.db_name = sqlite3.connect(filename)
        self.create_table()
        # self.cur = self.conn.cursor()

    def create_table(self):
        with self.get_connection() as conn:
            conn.execute("""
                         CREATE TABLE IF NOT EXISTS bank
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         client TEXT NOT NULL,
                         log TEXT NOT NULL,
                         account TEXT NOT NULL,
                         balance INTEGER NOT NULL,
                         currency TEXT NOT NULL,
                         status TEXT NOT NULL,
                         timestamp TEXT NOT NULL);
                         """)

            conn.commit()

    def get_connection(self):
        return sqlite3.connect('bank.db')

    def add_entry(self, client_name, log, account, balance, currency, status):
        timestamp = date.today()

        with self.get_connection() as conn:
            conn.execute("""
                        INSERT INTO bank (client, log, account, balance, currency, status, timestamp)
                        VALUES (?, ?, ?, ?, ?, ?, ?);
                        """, (client_name, log, account, balance, currency, status, timestamp))
            conn.commit()

    def show_table(self, filtr, value):    
        match filtr:
            case 'name':
                res = self.selection_by_names(value)
            case 'account':
                res = self.selection_by_accounts(value)
            case 'date':
                res = self.selection_by_dates(value)
            case 'status':
                res = self.selection_by_status(value)
            case _:
                res = "SELECT * FROM bank;"
        return res

    def selection_by_id(self, *args):
        placeholders = ','.join('?' for _ in args)

        with self.get_connection() as conn:
            conn.execute(f"SELECT * FROM bank WHERE id IN ({placeholders});", tuple(args))

            cursor = conn.cursor()
            return cursor.fetchall()
        
    def selection_by_names(self, *args):
        placeholders = ','.join('?' for _ in args)

        with self.get_connection() as conn:
            conn.execute(f"SELECT * FROM bank WHERE client IN ({placeholders});", tuple(args))

            cursor = conn.cursor()
            return cursor.fetchall()

    def selection_by_accounts(self, *args):
        placeholders = ','.join('?' for _ in args)

        with self.get_connection() as conn:
            conn.execute(f"SELECT * FROM bank WHERE account IN ({placeholders});", tuple(args))

            cursor = conn.cursor()
            return cursor.fetchall()

    def selection_by_currency(self, *args):
        placeholders = ','.join('?' for _ in args)

        with self.get_connection() as conn:
            conn.execute(f"SELECT * FROM bank WHERE currency IN ({placeholders});", tuple(args))

            cursor = conn.cursor()
            return cursor.fetchall()

    def selection_by_dates(self, *args):
        if len(args) == 1:
            date_from = args[0]
            date_to = args[0]
        elif len(args) == 2:
            date_from = args[0]
            date_to = args[1]
        with self.get_connection() as conn:
            conn.execute(f"SELECT * FROM bank WHERE timestamp BETWEEN ? AND ?;", (date_from, date_to))

            cursor = conn.cursor()
            return cursor.fetchall()
        
    def selection_by_status(self, status):
        with self.get_connection() as conn:
            conn.execute(f"SELECT * FROM bank WHERE status = ?;", (status, ))

            cursor = conn.cursor()
            return cursor.fetchall()        
    
    def delete_table(self):
        with self.get_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS bank;")
            conn.commit()

    def delete_rows(self, parametr, value):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM bank WHERE ? = ?;", (parametr, value))
            conn.commit()