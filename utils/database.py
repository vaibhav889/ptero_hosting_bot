import sqlite3
import os

DB_FILE = os.path.join("data", "users.db")

class DB:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cur = self.conn.cursor()
        self._create_tables()

    def _create_tables(self):
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                discord_id INTEGER PRIMARY KEY,
                panel_id INTEGER NOT NULL,
                email TEXT NOT NULL,
                banned INTEGER DEFAULT 0
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS servers (
                server_id TEXT PRIMARY KEY,
                owner_id INTEGER
            )
        """)
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS shared_access (
                server_id TEXT,
                user_id INTEGER
            )
        """)
        self.conn.commit()

    def add_user(self, discord_id: int, panel_id: int, email: str):
        self.cur.execute("INSERT OR REPLACE INTO users (discord_id, panel_id, email) VALUES (?, ?, ?)",
                         (discord_id, panel_id, email))
        self.conn.commit()

    def get_user(self, discord_id: int):
        result = self.cur.execute("SELECT * FROM users WHERE discord_id = ?", (discord_id,)).fetchone()
        if result:
            return {"discord_id": result[0], "panel_id": result[1], "email": result[2], "banned": result[3]}
        return None

    def list_users(self):
        return [
            {"discord_id": row[0], "panel_id": row[1], "email": row[2], "banned": row[3]}
            for row in self.cur.execute("SELECT * FROM users").fetchall()
        ]

    def ban_user(self, discord_id: int):
        self.cur.execute("UPDATE users SET banned = 1 WHERE discord_id = ?", (discord_id,))
        self.conn.commit()

    def unban_user(self, discord_id: int):
        self.cur.execute("UPDATE users SET banned = 0 WHERE discord_id = ?", (discord_id,))
        self.conn.commit()

    def is_banned(self, discord_id: int):
        result = self.cur.execute("SELECT banned FROM users WHERE discord_id = ?", (discord_id,)).fetchone()
        return result and result[0] == 1

    def add_server(self, server_id: str, owner_id: int):
        self.cur.execute("INSERT OR REPLACE INTO servers (server_id, owner_id) VALUES (?, ?)",
                         (server_id, owner_id))
        self.conn.commit()

    def delete_server(self, server_id: str):
        self.cur.execute("DELETE FROM servers WHERE server_id = ?", (server_id,))
        self.cur.execute("DELETE FROM shared_access WHERE server_id = ?", (server_id,))
        self.conn.commit()

    def server_exists(self, server_id: str, owner_id: int):
        result = self.cur.execute(
            "SELECT 1 FROM servers WHERE server_id = ? AND owner_id = ?",
            (server_id, owner_id)
        ).fetchone()
        return result is not None

    def get_owned_servers(self, discord_id: int):
        rows = self.cur.execute("SELECT server_id FROM servers WHERE owner_id = ?", (discord_id,)).fetchall()
        return [r[0] for r in rows]

    def share_server(self, server_id: str, user_id: int):
        self.cur.execute("INSERT INTO shared_access (server_id, user_id) VALUES (?, ?)",
                         (server_id, user_id))
        self.conn.commit()

    def unshare_server(self, server_id: str, user_id: int):
        self.cur.execute("DELETE FROM shared_access WHERE server_id = ? AND user_id = ?",
                         (server_id, user_id))
        self.conn.commit()

    def get_shared_servers(self, user_id: int):
        rows = self.cur.execute("SELECT server_id FROM shared_access WHERE user_id = ?", (user_id,)).fetchall()
        return [r[0] for r in rows]

    def get_shared_users(self, server_id: str):
        rows = self.cur.execute("SELECT user_id FROM shared_access WHERE server_id = ?", (server_id,)).fetchall()
        return [r[0] for r in rows]
