from pathlib import Path
import sqlite3


class DatabaseManager:
    DB_DIR = Path("data")
    DB_FILE = DB_DIR / "maxky_pos.db"

    @classmethod
    def initialize(cls):
        """สร้างโฟลเดอร์และไฟล์ฐานข้อมูล"""
        cls.DB_DIR.mkdir(exist_ok=True)

        conn = sqlite3.connect(cls.DB_FILE)
        conn.close()

    @classmethod
    def connect(cls):
        conn = sqlite3.connect(cls.DB_FILE)
        conn.row_factory = sqlite3.Row
        return conn