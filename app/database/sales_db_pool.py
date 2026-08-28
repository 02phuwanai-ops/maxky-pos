import os
import pymysql
from dbutils.pooled_db import PooledDB


# ==========================================
# อ่านรหัสผ่านจาก Environment Variable
# ==========================================

DB_PASSWORD = os.getenv("MYSQL_PASSWORD")

if not DB_PASSWORD:
    raise RuntimeError("❌ ไม่พบ MYSQL_PASSWORD ใน Environment Variables")


# ==========================================
# Connection Pool เชื่อมต่อ Aiven Cloud MySQL
# ==========================================

DB_POOL = PooledDB(
    creator=pymysql,

    maxconnections=10,
    mincached=2,
    maxcached=5,

    blocking=True,
    ping=1,

    host="mysql-18d9fbcf-phuwanai-ot-note-pro-v1.j.aivencloud.com",
    user="avnadmin",
    password=DB_PASSWORD,
    database="defaultdb",
    port=10981,

    autocommit=True,

    cursorclass=pymysql.cursors.DictCursor,
)


def get_db_connection():
    """ดึง Connection จาก Pool ออกมาใช้งาน"""
    return DB_POOL.connection()


def get_recent_sales(limit=10):
    """ฟังก์ชันดึงรายการขายล่าสุดแบบเร็ว"""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM sales ORDER BY id DESC LIMIT %s",
                (limit,)
            )

            return cursor.fetchall()

    finally:
        # คืน Connection กลับเข้า Pool
        conn.close()


def get_today_summary():
    """ดึงสรุปยอดขายวันนี้แบบเร็ว"""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COALESCE(SUM(total_amount), 0) AS total_revenue,
                    COALESCE(SUM(total_items), 0) AS total_items,
                    COUNT(id) AS total_transactions
                FROM sales
                WHERE DATE(created_at) = CURDATE()
            """)

            return (
                cursor.fetchone()
                or {
                    "total_revenue": 0,
                    "total_items": 0,
                    "total_transactions": 0
                }
            )

    finally:
        conn.close()