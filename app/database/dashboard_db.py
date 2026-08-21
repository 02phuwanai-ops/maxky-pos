import sqlite3


DB = "data/maxky_pos.db"


def get_dashboard():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            IFNULL(SUM(price),0),
            IFNULL(SUM(profit),0)
        FROM sales
        WHERE DATE(created_at)=DATE('now','localtime')
    """)

    data = cursor.fetchone()

    conn.close()

    return data


def get_stock_count():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT IFNULL(SUM(quantity),0)
        FROM stock
    """)

    total = cursor.fetchone()[0]

    conn.close()

    return total


def get_low_stock_count():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM stock
        WHERE quantity<=3
    """)

    total = cursor.fetchone()[0]

    conn.close()

    return total


def get_low_stock_items():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category,
            size,
            quantity
        FROM stock
        WHERE quantity<=3
        ORDER BY quantity ASC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows


def get_top_product():

    conn = sqlite3.connect(DB)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category || ' ' || size
        FROM sales
        GROUP BY category,size
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    conn.close()

    if row:
        return row[0]

    return "-"
import sqlite3


def get_top_sales():

    conn = sqlite3.connect("data/maxky_pos.db")

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            category,
            size,
            COUNT(*)
        FROM sales
        GROUP BY category,size
        ORDER BY COUNT(*) DESC
        LIMIT 5
    """)

    data = cursor.fetchall()

    conn.close()

    return data