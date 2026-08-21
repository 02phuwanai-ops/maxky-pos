import sqlite3

DB_NAME = "data/maxky_pos.db"


def create_stock_table():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS stock (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

        category TEXT,

        size TEXT,

        quantity INTEGER DEFAULT 0

    )
    """)

    conn.commit()
    conn.close()


def reduce_stock(category, size):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE stock

        SET quantity = quantity - 1

        WHERE category = ?

        AND size = ?

        AND quantity > 0
        """,
        (
            category,
            size
        )
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

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE stock

        SET quantity = quantity + 1

        WHERE category=?

        AND size=?
        """,
        (
            category,
            size
        )
    )

    conn.commit()

    affected = cursor.rowcount

    conn.close()

    return affected > 0


def get_stock(category, size):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

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

    result = cursor.fetchone()

    conn.close()

    if result:

        return result[0]

    return 0


def get_sizes():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT size
        FROM stock
        ORDER BY size
    """)

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]


def get_sizes_by_product(category):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT size

        FROM stock

        WHERE category=?

        AND quantity>0

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
        (
            category,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return [row[0] for row in rows]


# ==========================================
# Build 0.81
# Dashboard
#
# แสดงเฉพาะ Stock ของสินค้าที่มีอยู่ใน Products
# ==========================================

def get_all_stock():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            stock.category,
            stock.size,
            stock.quantity

        FROM stock

        INNER JOIN products
            ON TRIM(products.category)
            =
            TRIM(stock.category)

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

    return rows


def get_total_stock():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT IFNULL(SUM(quantity),0)
        FROM stock
        """
    )

    total = cursor.fetchone()[0]

    conn.close()

    return total


def get_low_stock(limit=2):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            category,
            size,
            quantity
        FROM stock
        WHERE quantity<=?
        ORDER BY quantity ASC
        """,
        (
            limit,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================
# Build 0.82
# Stock Group Dashboard
#
# แสดงเฉพาะสินค้าที่มีอยู่ใน Products
# ==========================================

def get_stock_groups():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            stock.category,
            stock.size,
            stock.quantity

        FROM stock

        INNER JOIN products
            ON TRIM(products.category)
            =
            TRIM(stock.category)

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


    for category, size, quantity in rows:

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

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    sizes = [

        "S",
        "M",
        "L",
        "XL",
        "2XL",
        "3XL"

    ]

    for size in sizes:

        cursor.execute(
            """
            INSERT OR IGNORE INTO stock
            (
                category,
                size,
                quantity
            )

            VALUES
            (
                ?,
                ?,
                0
            )
            """,
            (
                category,
                size
            )
        )

    conn.commit()

    conn.close()

# ==========================================
# STEP 2
# ล้าง Stock ที่ไม่มีสินค้าใน Products แล้ว
# ==========================================

def cleanup_orphan_stock():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    try:

        cursor.execute(
            """
            DELETE FROM stock

            WHERE NOT EXISTS (

                SELECT 1

                FROM products

                WHERE
                    TRIM(products.category)
                    =
                    TRIM(stock.category)

            )
            """
        )

        deleted = cursor.rowcount

        conn.commit()

        print(
            f"🧹 Cleanup Stock: ลบรายการเก่า {deleted} รายการ"
        )

        return deleted

    except Exception as e:

        conn.rollback()

        print(
            "❌ CLEANUP STOCK ERROR:",
            e
        )

        return 0

    finally:

        conn.close()