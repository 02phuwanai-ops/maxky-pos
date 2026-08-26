import pymysql
from datetime import datetime
from app.database.db import get_db_connection


# ==========================================
# สร้างตารางรับสต็อก
# ==========================================

def create_receive_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_receive (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(255),
        size VARCHAR(100),
        quantity INT,
        created_at DATETIME
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()


# ==========================================
# เพิ่มสต็อก + บันทึกประวัติ
# ==========================================

def add_stock(category, size, quantity):
    create_receive_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. ตรวจสอบว่ามี Stock row อยู่หรือไม่
    cursor.execute(
        """
        SELECT quantity
        FROM stock
        WHERE category=%s AND size=%s
        """,
        (category, size)
    )

    row = cursor.fetchone()

    # 2. ถ้ามี Stock อยู่แล้ว → เพิ่มจำนวน / ถ้ายังไม่มี → สร้างใหม่
    if row:
        cursor.execute(
            """
            UPDATE stock
            SET quantity = quantity + %s
            WHERE category=%s AND size=%s
            """,
            (quantity, category, size)
        )
    else:
        cursor.execute(
            """
            INSERT INTO stock (category, size, quantity)
            VALUES (%s, %s, %s)
            """,
            (category, size, quantity)
        )

    # 3. เก็บประวัติรับสินค้า
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO stock_receive (category, size, quantity, created_at)
        VALUES (%s, %s, %s, %s)
        """,
        (category, size, quantity, now_str)
    )

    conn.commit()
    conn.close()


# ==========================================
# ดึงประวัติการรับสินค้าล่าสุด
# ==========================================

def get_recent_receive(limit=10):
    create_receive_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            created_at,
            category,
            size,
            quantity
        FROM stock_receive
        ORDER BY id DESC
        LIMIT %s
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    # แปลงผลลัพธ์เป็น Tuple หากคอร์เซอร์คืนค่าแบบ Dict
    if rows and isinstance(rows[0], dict):
        return [
            (
                r["created_at"],
                r["category"],
                r["size"],
                r["quantity"]
            )
            for r in rows
        ]

    return rows