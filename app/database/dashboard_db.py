import os
import pymysql

def get_db_connection():
    """สร้าง Connection เชื่อมต่อไปยัง MySQL (Aiven)"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        autocommit=True
    )

def get_dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()

    # ปรับใช้ CURDATE() ของ MySQL แทน DATE('now','localtime')
    cursor.execute("""
        SELECT
            COUNT(*),
            IFNULL(SUM(price), 0),
            IFNULL(SUM(profit), 0)
        FROM sales
        WHERE DATE(created_at) = CURDATE()
    """)

    data = cursor.fetchone()
    conn.close()
    
    # แปลง Decimal จาก MySQL ให้เป็น float เพื่อหลีกเลี่ยงปัญหา Data Type
    return (
        data[0],
        float(data[1]) if data[1] is not None else 0.0,
        float(data[2]) if data[2] is not None else 0.0
    )


def get_stock_count():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT IFNULL(SUM(quantity), 0)
        FROM stock
    """)

    total = float(cursor.fetchone()[0])
    conn.close()
    return total


def get_low_stock_count():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM stock
        WHERE quantity <= 3
    """)

    total = cursor.fetchone()[0]
    conn.close()
    return total


def get_low_stock_items():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category,
            size,
            quantity
        FROM stock
        WHERE quantity <= 3
        ORDER BY quantity ASC
    """)

    rows = cursor.fetchall()
    conn.close()
    return rows


def get_top_product():
    conn = get_db_connection()
    cursor = conn.cursor()

    # ปรับ Syntax รวมคำ จาก || มาใช้ CONCAT() ตามหลัก MySQL
    cursor.execute("""
        SELECT
            CONCAT(category, ' ', size)
        FROM sales
        GROUP BY category, size
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row:
        return row[0]

    return "-"


def get_top_sales():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category,
            size,
            COUNT(*)
        FROM sales
        GROUP BY category, size
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    data = cursor.fetchall()
    conn.close()
    return data