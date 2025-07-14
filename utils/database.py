import sqlite3
import os

DB_FILE = "data/users.db"

class DB:
    def __init__(self):
        os.makedirs("data", exist_ok=True)  # Ensure 'data' directory exists
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                panel_id INTEGER,
                email TEXT,
                servers TEXT DEFAULT '',
                shared TEXT DEFAULT '',
                banned INTEGER DEFAULT 0
            )
        ''')
        self.conn.commit()

    def add_user(self, discord_id, panel_id, email):
        self.conn.execute(
            "INSERT OR IGNORE INTO users (discord_id, panel_id, email) VALUES (?, ?, ?)",
            (discord_id, panel_id, email),
        )
        self.conn.commit()

    def get_user(self, discord_id):
        cursor = self.conn.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        return cursor.fetchone()

    def set_banned(self, discord_id, banned):
        self.conn.execute("UPDATE users SET banned = ? WHERE discord_id = ?", (banned, discord_id))
        self.conn.commit()

    def get_all_users(self):
        cursor = self.conn.execute("SELECT * FROM users")
        return cursor.fetchall()

    def update_servers(self, discord_id, servers):
        self.conn.execute("UPDATE users SET servers = ? WHERE discord_id = ?", (servers, discord_id))
        self.conn.commit()

    def update_shared(self, discord_id, shared):
        self.conn.execute("UPDATE users SET shared = ? WHERE discord_id = ?", (shared, discord_id))
        self.conn.commit()
