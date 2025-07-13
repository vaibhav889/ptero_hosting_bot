import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "users.db")

class Database:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self.conn = sqlite3.connect(DB_PATH)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                discord_id TEXT PRIMARY KEY,
                email TEXT,
                ptero_user_id INTEGER,
                plan TEXT DEFAULT 'default'
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS shared_access (
                owner_id TEXT,
                target_id TEXT,
                server_id TEXT,
                PRIMARY KEY (owner_id, target_id, server_id)
            )
        ''')
        self.conn.commit()

    def add_user(self, discord_id, email, ptero_user_id):
        self.cursor.execute(
            "INSERT OR REPLACE INTO users (discord_id, email, ptero_user_id) VALUES (?, ?, ?)",
            (discord_id, email, ptero_user_id)
        )
        self.conn.commit()

    def get_user(self, discord_id):
        self.cursor.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,))
        return self.cursor.fetchone()

    def share_server(self, owner_id, target_id, server_id):
        self.cursor.execute(
            "INSERT OR REPLACE INTO shared_access (owner_id, target_id, server_id) VALUES (?, ?, ?)",
            (owner_id, target_id, server_id)
        )
        self.conn.commit()

    def unshare_server(self, owner_id, target_id, server_id):
        self.cursor.execute(
            "DELETE FROM shared_access WHERE owner_id = ? AND target_id = ? AND server_id = ?",
            (owner_id, target_id, server_id)
        )
        self.conn.commit()

    def get_shared_servers(self, target_id):
        self.cursor.execute(
            "SELECT server_id FROM shared_access WHERE target_id = ?", (target_id,)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def close(self):
        self.conn.close()
