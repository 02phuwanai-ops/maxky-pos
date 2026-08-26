import os
import pymysql
from pymysql.cursors import DictCursor

def get_db_connection():
    """สร้างการเชื่อมต่อฐานข้อมูล MySQL (คืนค่า Cursor แบบ Dictionary/Row)"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        cursorclass=DictCursor,
        autocommit=True
    )

class DatabaseManager:
    @classmethod
    def initialize(cls):
        """ตรวจสอบและทดสอบการเชื่อมต่อฐานข้อมูล MySQL"""
        try:
            conn = get_db_connection()
            print("✅ [MySQL] Successfully connected to Database.")
            conn.close()
        except Exception as e:
            print(f"❌ [MySQL] Connection Failed: {e}")

    @classmethod
    def connect(cls):
        """ดึง Connection สำหรับรองรับโค้ดเก่าที่เรียกใช้ DatabaseManager.connect()"""
        return get_db_connection()