import pymysql
from app.database.db import get_db_connection


def init_pos_db():
    """สร้างตารางสำหรับฝั่ง POS หากยังไม่มีใน MySQL"""
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. ตาราง stock
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(100) NOT NULL,
            size VARCHAR(50) NOT NULL,
            quantity INT DEFAULT 0,
            price DECIMAL(10,2) DEFAULT 0.00,
            cost DECIMAL(10,2) DEFAULT 0.00
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # 2. ตาราง sales
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(100) NOT NULL,
            size VARCHAR(50) NOT NULL,
            cost DECIMAL(10,2) DEFAULT 0.00,
            price DECIMAL(10,2) NOT NULL,
            profit DECIMAL(10,2) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            event_name VARCHAR(100) DEFAULT '',
            payment_method VARCHAR(100) DEFAULT 'เงินสด',
            station_name VARCHAR(100) DEFAULT 'จุดขายที่ 1',
            shift_id INT,
            is_closed INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.close()


def get_dashboard():
    init_pos_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            IFNULL(SUM(price), 0),
            IFNULL(SUM(profit), 0)
        FROM sales
        WHERE DATE(created_at) = CURDATE() AND is_closed = 0
    """)

    data = cursor.fetchone()
    conn.close()

    # รองรับผลลัพธ์ทั้งแบบ DictCursor และ Tuple Normal Cursor
    if isinstance(data, dict):
        cnt = data.get("COUNT(*)", 0)
        revenue = data.get("IFNULL(SUM(price), 0)", 0.0)
        profit = data.get("IFNULL(SUM(profit), 0)", 0.0)
    else:
        cnt = data[0] if data else 0
        revenue = data[1] if data else 0.0
        profit = data[2] if data else 0.0

    return (
        cnt,
        float(revenue) if revenue is not None else 0.0,
        float(profit) if profit is not None else 0.0
    )


def get_stock_count():
    init_pos_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT IFNULL(SUM(quantity), 0) AS total
        FROM stock
    """)

    row = cursor.fetchone()
    conn.close()

    if isinstance(row, dict):
        total = row.get("total", 0)
    else:
        total = row[0] if row else 0

    return float(total)


def get_low_stock_count():
    init_pos_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) AS total
        FROM stock
        WHERE quantity <= 3
    """)

    row = cursor.fetchone()
    conn.close()

    if isinstance(row, dict):
        return row.get("total", 0)
    return row[0] if row else 0


def get_low_stock_items():
    init_pos_db()
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

    if rows and isinstance(rows[0], dict):
        return [(r["category"], r["size"], r["quantity"]) for r in rows]

    return rows


def get_top_product():
    init_pos_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            CONCAT(category, ' ', size) AS item_name
        FROM sales
        GROUP BY category, size
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    row = cursor.fetchone()
    conn.close()

    if row:
        if isinstance(row, dict):
            return row.get("item_name", "-")
        return row[0]

    return "-"


def get_top_sales():
    init_pos_db()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category,
            size,
            COUNT(*) AS total_count
        FROM sales
        GROUP BY category, size
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    rows = cursor.fetchall()
    conn.close()

    if rows and isinstance(rows[0], dict):
        return [(r["category"], r["size"], r["total_count"]) for r in rows]

    return rows