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

    def show_table(self, select_col, **kwargs):  
        with self.get_connection() as conn: 
            if select_col or kwargs:
                cursor = self.select_by_column(select_col, conn, **kwargs)
            else:
                cursor = conn.execute("SELECT * FROM bank;")
            return cursor.fetchall()
        
    @staticmethod
    def get_sql_condition(**kwargs):
        where_clauses = []
        params = []

        for key, values in kwargs.items():
            if isinstance(values, (tuple, list)):
                placeholders = ', '.join(['?'] * len(values))
                where_clauses.append(f"{key} IN ({placeholders})")
                params.extend(values)
            else:
                where_clauses.append(f"{key} = ?")
                params.append(values)
        return where_clauses, params
    
    def select_by_column(self, select_col, conn, **kwargs):
        select = ', '.join(select_col) if select_col else '*'
        sql = f"SELECT DISTINCT {select} FROM bank;"

        where_clauses, params = Database.get_sql_condition(**kwargs)

        if where_clauses:
            where = ' AND '.join(where_clauses)
            sql = f"SELECT DISTINCT {select} FROM bank WHERE {where}"
        cursor = conn.execute(sql, tuple(params))
        return cursor
    
    def update_table(self, col_name, new_val, **kwargs):
        with self.get_connection() as conn: 
            sql = f"UPDATE bank SET {col_name} = ?;"

            where_clauses, params = Database.get_sql_condition(**kwargs)

            if where_clauses:
                where = ' AND '.join(where_clauses)
                sql = f"UPDATE bank SET {col_name} = ? WHERE {where};"

            cursor = conn.execute(sql, (new_val, *params))
            return cursor

    def delete_from_db(self, **kwargs):
        with self.get_connection() as conn:
            sql = f"DELETE FROM bank;"
            if not kwargs:
                cursor = conn.execute(sql)
            else:
                where_clauses, params = Database.get_sql_condition(**kwargs)

                if where_clauses:
                    where = ' AND '.join(where_clauses) 
                    sql = f"DELETE FROM bank WHERE {where}"
                cursor = conn.execute(sql, tuple(params))
            return cursor 