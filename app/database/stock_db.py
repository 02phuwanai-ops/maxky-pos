import pymysql
from app.database.db import get_db_connection


def create_stock_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(100) NOT NULL,
            size VARCHAR(50) NOT NULL,
            quantity INT DEFAULT 0,
            price DECIMAL(10,2) DEFAULT 0.00,
            cost DECIMAL(10,2) DEFAULT 0.00,
            UNIQUE KEY idx_category_size (category, size)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()


def reduce_stock(category, size):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE stock
        SET quantity = quantity - 1
        WHERE category = %s
        AND size = %s
        AND quantity > 0
        """,
        (category, size)
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


# ==========================================
# Build 0.79
# คืน Stock
# ==========================================

def increase_stock(category, size):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE stock
        SET quantity = quantity + 1
        WHERE category = %s
        AND size = %s
        """,
        (category, size)
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


def get_stock(category, size):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT quantity
        FROM stock
        WHERE category = %s
        AND size = %s
        """,
        (category, size)
    )

    result = cursor.fetchone()
    conn.close()

    if result:
        if isinstance(result, dict):
            return result.get("quantity", 0)
        return result[0]

    return 0


def get_sizes():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT size
        FROM stock
        ORDER BY size
    """)

    rows = cursor.fetchall()
    conn.close()

    if rows and isinstance(rows[0], dict):
        return [row["size"] for row in rows]

    return [row[0] for row in rows]


def get_sizes_by_product(category):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT size
        FROM stock
        WHERE category = %s
        AND quantity > 0
        ORDER BY
            CASE size
                WHEN 'S' THEN 1
                WHEN 'M' THEN 2
                WHEN 'L' THEN 3
                WHEN 'XL' THEN 4
                WHEN '2XL' THEN 5
                WHEN '3XL' THEN 6
                ELSE 99
            END
        """,
        (category,)
    )

    rows = cursor.fetchall()
    conn.close()

    if rows and isinstance(rows[0], dict):
        return [row["size"] for row in rows]

    return [row[0] for row in rows]


# ==========================================
# Build 0.81
# Dashboard (แสดงเฉพาะ Stock ของสินค้าที่มีใน Products)
# ==========================================

def get_all_stock():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            stock.category,
            stock.size,
            stock.quantity
        FROM stock
        INNER JOIN products
            ON TRIM(products.category) = TRIM(stock.category)
        ORDER BY
            stock.category,
            CASE stock.size
                WHEN 'S' THEN 1
                WHEN 'M' THEN 2
                WHEN 'L' THEN 3
                WHEN 'XL' THEN 4
                WHEN '2XL' THEN 5
                WHEN '3XL' THEN 6
                ELSE 99
            END
        """
    )

    rows = cursor.fetchall()
    conn.close()

    if rows and isinstance(rows[0], dict):
        return [(r["category"], r["size"], r["quantity"]) for r in rows]

    return rows


def get_total_stock():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT IFNULL(SUM(quantity), 0) AS total
        FROM stock
        """
    )

    row = cursor.fetchone()
    conn.close()

    if isinstance(row, dict):
        return float(row.get("total", 0))

    return float(row[0]) if row else 0.0


def get_low_stock(limit=2):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            category,
            size,
            quantity
        FROM stock
        WHERE quantity <= %s
        ORDER BY quantity ASC
        """,
        (limit,)
    )

    rows = cursor.fetchall()
    conn.close()

    if rows and isinstance(rows[0], dict):
        return [(r["category"], r["size"], r["quantity"]) for r in rows]

    return rows


# ==========================================
# Build 0.82
# Stock Group Dashboard
# ==========================================

def get_stock_groups():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            stock.category,
            stock.size,
            stock.quantity
        FROM stock
        INNER JOIN products
            ON TRIM(products.category) = TRIM(stock.category)
        ORDER BY
            stock.category,
            CASE stock.size
                WHEN 'S' THEN 1
                WHEN 'M' THEN 2
                WHEN 'L' THEN 3
                WHEN 'XL' THEN 4
                WHEN '2XL' THEN 5
                WHEN '3XL' THEN 6
                ELSE 99
            END
        """
    )

    rows = cursor.fetchall()
    conn.close()

    groups = {}

    for row in rows:
        if isinstance(row, dict):
            category = row["category"]
            size = row["size"]
            quantity = row["quantity"]
        else:
            category, size, quantity = row

        if category not in groups:
            groups[category] = []

        groups[category].append({
            "size": size,
            "quantity": quantity
        })

    return groups


# ==========================================
# Build 0.85
# สร้าง Stock เริ่มต้นของสินค้าใหม่
# ==========================================

def create_product_stock(category):
    create_stock_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    sizes = ["S", "M", "L", "XL", "2XL", "3XL"]

    for size in sizes:
        cursor.execute(
            """
            INSERT IGNORE INTO stock (category, size, quantity)
            VALUES (%s, %s, 0)
            """,
            (category, size)
        )

    conn.commit()
    conn.close()


# ==========================================
# STEP 2
# ล้าง Stock ที่ไม่มีสินค้าใน Products แล้ว
# ==========================================

def cleanup_orphan_stock():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            DELETE FROM stock
            WHERE NOT EXISTS (
                SELECT 1
                FROM products
                WHERE TRIM(products.category) = TRIM(stock.category)
            )
            """
        )

        deleted = cursor.rowcount
        conn.commit()

        print(f"🧹 Cleanup Stock: ลบรายการเก่า {deleted} รายการ")
        return deleted

    except Exception as e:
        conn.rollback()
        print("❌ CLEANUP STOCK ERROR:", e)
        return 0

    finally:
        conn.close()