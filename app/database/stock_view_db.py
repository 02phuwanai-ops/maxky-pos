import pymysql
from app.database.db import get_db_connection


# ==========================================
# ดึงข้อมูลสต็อกสินค้าทั้งหมด
# ==========================================
def get_stock_all():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    category,
                    size,
                    quantity
                FROM stock
                ORDER BY category, size
                """
            )
            data = cursor.fetchall()
        return data
    finally:
        conn.close()


# ==========================================
# ดึงข้อมูลสินค้าที่สต็อกใกล้หมด (<= 5)
# ==========================================
def get_low_stock():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    category,
                    size,
                    quantity
                FROM stock
                WHERE quantity <= 5
                ORDER BY quantity ASC
                """
            )
            data = cursor.fetchall()
        return data
    finally:
        conn.close()