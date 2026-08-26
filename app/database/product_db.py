import pymysql
from app.database.db import get_db_connection


# ==========================================
# Product Table
# ==========================================

def create_product_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Products
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(255) UNIQUE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    # Product Prices By Size
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_prices (
            id INT AUTO_INCREMENT PRIMARY KEY,
            product_id INT NOT NULL,
            size VARCHAR(50) NOT NULL,
            cost DECIMAL(10,2) DEFAULT 0.00,
            price DECIMAL(10,2) DEFAULT 0.00,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            UNIQUE KEY idx_product_size (product_id, size)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()


# ==========================================
# เพิ่มสินค้า
# ==========================================

def add_product(category):
    create_product_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products(category)
        VALUES(%s)
        """,
        (category,)
    )

    conn.commit()
    product_id = cursor.lastrowid
    conn.close()

    return product_id


# ==========================================
# เพิ่มราคาแต่ละไซส์
# ==========================================

def add_product_price(product_id, size, cost, price):
    create_product_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO product_prices(
            product_id,
            size,
            cost,
            price
        )
        VALUES(%s, %s, %s, %s)
        """,
        (
            product_id,
            size,
            cost,
            price
        )
    )

    conn.commit()
    conn.close()


# ==========================================
# รายชื่อสินค้า
# ==========================================

def get_products():
    create_product_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            category
        FROM products
        ORDER BY category
    """)

    rows = cursor.fetchall()
    conn.close()

    # คืนค่ารองรับทั้ง Tuple และ Dict Cursor
    if rows and isinstance(rows[0], dict):
        return [(r["id"], r["category"]) for r in rows]

    return rows


# ==========================================
# ราคาทั้งหมดของสินค้า
# ==========================================

def get_product_sizes(product_id):
    create_product_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            size,
            cost,
            price
        FROM product_prices
        WHERE product_id = %s
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
        (product_id,)
    )

    rows = cursor.fetchall()
    conn.close()

    if rows and isinstance(rows[0], dict):
        return [(r["id"], r["size"], float(r["cost"]), float(r["price"])) for r in rows]

    return rows


# ==========================================
# ใช้ตอนขาย (ราคาแยกตามสินค้า + ไซส์)
# ==========================================

def get_product_price(category, size):
    create_product_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            pp.cost,
            pp.price
        FROM products p
        INNER JOIN product_prices pp
            ON p.id = pp.product_id
        WHERE
            TRIM(p.category) = TRIM(%s)
        AND
            TRIM(pp.size) = TRIM(%s)
        LIMIT 1
        """,
        (category, size)
    )

    row = cursor.fetchone()
    conn.close()

    if row:
        if isinstance(row, dict):
            return (float(row.get("cost", 0)), float(row.get("price", 0)))
        return row

    return None


# ==========================================
# แก้ไขราคาแต่ละไซส์
# ==========================================

def update_product_price(price_id, cost, price):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE product_prices
        SET
            cost = %s,
            price = %s
        WHERE id = %s
        """,
        (cost, price, price_id)
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


# ==========================================
# ลบราคาไซส์
# ==========================================

def delete_product_price(price_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM product_prices
        WHERE id = %s
        """,
        (price_id,)
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0


# ==========================================
# ลบสินค้า (พร้อมลบ Stock และราคา)
# ==========================================

def delete_product(product_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        # ----------------------------------
        # หา category ก่อนลบ
        # ----------------------------------

        cursor.execute(
            """
            SELECT category
            FROM products
            WHERE id = %s
            LIMIT 1
            """,
            (product_id,)
        )

        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        category = row.get("category") if isinstance(row, dict) else row[0]

        # ----------------------------------
        # 1. ลบ Stock ของสินค้า
        # ----------------------------------

        cursor.execute(
            """
            DELETE FROM stock
            WHERE TRIM(category) = TRIM(%s)
            """,
            (category,)
        )

        # ----------------------------------
        # 2. ลบราคาของสินค้า
        # ----------------------------------

        cursor.execute(
            """
            DELETE FROM product_prices
            WHERE product_id = %s
            """,
            (product_id,)
        )

        # ----------------------------------
        # 3. ลบสินค้า
        # ----------------------------------

        cursor.execute(
            """
            DELETE FROM products
            WHERE id = %s
            """,
            (product_id,)
        )

        affected = cursor.rowcount

        conn.commit()
        conn.close()

        return affected > 0

    except Exception as e:
        conn.rollback()
        conn.close()
        print("DELETE PRODUCT ERROR:", e)
        return False


# ==========================================
# ค้นหาสินค้าจากชื่อ
# ==========================================

def get_product(category):
    create_product_table()
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category
        FROM products
        WHERE category = %s
        LIMIT 1
        """,
        (category,)
    )

    row = cursor.fetchone()
    conn.close()

    if row and isinstance(row, dict):
        return (row["id"], row["category"])

    return row


# ==========================================
# แก้ชื่อสินค้า
# ==========================================

def update_product_name(product_id, category):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products
        SET category = %s
        WHERE id = %s
        """,
        (category, product_id)
    )

    conn.commit()
    affected = cursor.rowcount
    conn.close()

    return affected > 0