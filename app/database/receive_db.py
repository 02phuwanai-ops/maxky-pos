import sqlite3
from datetime import datetime


DB_NAME = "data/maxky_pos.db"



def create_receive_table():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock_receive (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        category TEXT,

        size TEXT,

        quantity INTEGER,

        created_at TEXT

    )
    """)


    conn.commit()

    conn.close()



def add_stock(category, size, quantity):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    # ======================================
    # ตรวจว่ามี Stock row อยู่หรือไม่
    # ======================================

    cursor.execute(
        """
        SELECT quantity
        FROM stock
        WHERE category=?
        AND size=?
        """,
        (
            category,
            size
        )
    )

    row = cursor.fetchone()


    # ======================================
    # ถ้ามี Stock อยู่แล้ว → เพิ่มจำนวน
    # ======================================

    if row:

        cursor.execute(
            """
            UPDATE stock

            SET quantity = quantity + ?

            WHERE category=?
            AND size=?
            """,
            (
                quantity,
                category,
                size
            )
        )


    # ======================================
    # ถ้ายังไม่มี Stock → สร้างใหม่
    # ======================================

    else:

        cursor.execute(
            """
            INSERT INTO stock
            (
                category,
                size,
                quantity
            )

            VALUES (?,?,?)
            """,
            (
                category,
                size,
                quantity
            )
        )


    # ======================================
    # เก็บประวัติรับสินค้า
    # ======================================

    cursor.execute(
        """
        INSERT INTO stock_receive
        (
            category,
            size,
            quantity,
            created_at
        )

        VALUES (?,?,?,?)
        """,
        (
            category,
            size,
            quantity,
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )
    )


    conn.commit()

    conn.close()

def get_recent_receive(limit=10):

    conn = sqlite3.connect(DB_NAME)

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

        LIMIT ?
        """,
        (limit,)
    )

    rows = cursor.fetchall()

    conn.close()

    return rows