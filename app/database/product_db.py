import sqlite3


DB_NAME = "data/maxky_pos.db"


# ==========================================
# Product Table
# ==========================================

def create_product_table():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    # --------------------------------------
    # Products
    # --------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            category TEXT UNIQUE

        )
    """)

    # --------------------------------------
    # Product Prices By Size
    # --------------------------------------

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_prices (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            product_id INTEGER NOT NULL,

            size TEXT NOT NULL,

            cost REAL DEFAULT 0,

            price REAL DEFAULT 0,

            FOREIGN KEY(product_id)
            REFERENCES products(id)

        )
    """)

    # ป้องกันสินค้าเดียวกันมีราคาไซส์เดียวกันซ้ำ
    cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS
        idx_product_size
        ON product_prices(product_id, size)
    """)

    conn.commit()

    conn.close()


# ==========================================
# เพิ่มสินค้า
# ==========================================

def add_product(category):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO products(category)

        VALUES(?)
        """,
        (
            category,
        )
    )

    conn.commit()

    product_id = cursor.lastrowid

    conn.close()

    return product_id


# ==========================================
# เพิ่มราคาแต่ละไซส์
# ==========================================

def add_product_price(
    product_id,
    size,
    cost,
    price
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO product_prices(

            product_id,
            size,
            cost,
            price

        )

        VALUES(?,?,?,?)
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

    conn = sqlite3.connect(DB_NAME)

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

    return rows


# ==========================================
# ราคาทั้งหมดของสินค้า
# ==========================================

def get_product_sizes(product_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            id,
            size,
            cost,
            price

        FROM product_prices

        WHERE product_id=?

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
            product_id,
        )
    )

    rows = cursor.fetchall()

    conn.close()

    return rows


# ==========================================
# ใช้ตอนขาย
# ราคาแยกตามสินค้า + ไซส์
# ==========================================

def get_product_price(
    category,
    size
):

    conn = sqlite3.connect(DB_NAME)

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
            TRIM(p.category) = TRIM(?)

        AND
            TRIM(pp.size) = TRIM(?)

        LIMIT 1
        """,
        (
            category,
            size
        )
    )

    row = cursor.fetchone()

    conn.close()

    return row


# ==========================================
# แก้ราคา
# ==========================================

def update_product_price(
    price_id,
    cost,
    price
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE product_prices

        SET

            cost=?,

            price=?

        WHERE id=?
        """,
        (
            cost,
            price,
            price_id
        )
    )

    conn.commit()

    affected = cursor.rowcount

    conn.close()

    return affected > 0


# ==========================================
# ลบราคาไซส์
# ==========================================

def delete_product_price(price_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM product_prices

        WHERE id=?
        """,
        (
            price_id,
        )
    )

    conn.commit()

    affected = cursor.rowcount

    conn.close()

    return affected > 0


# ==========================================
# ลบสินค้า
#
# สำคัญ:
# ลบ Stock ของสินค้าด้วย
# ==========================================

def delete_product(product_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    try:

        # ----------------------------------
        # หา category ก่อนลบ
        # ----------------------------------

        cursor.execute(
            """
            SELECT

                category

            FROM products

            WHERE id=?

            LIMIT 1
            """,
            (
                product_id,
            )
        )

        row = cursor.fetchone()

        if not row:

            conn.close()

            return False


        category = row[0]


        # ----------------------------------
        # 1. ลบ Stock ของสินค้า
        # ----------------------------------

        cursor.execute(
            """
            DELETE FROM stock

            WHERE TRIM(category) = TRIM(?)
            """,
            (
                category,
            )
        )


        # ----------------------------------
        # 2. ลบราคาของสินค้า
        # ----------------------------------

        cursor.execute(
            """
            DELETE FROM product_prices

            WHERE product_id=?
            """,
            (
                product_id,
            )
        )


        # ----------------------------------
        # 3. ลบสินค้า
        # ----------------------------------

        cursor.execute(
            """
            DELETE FROM products

            WHERE id=?
            """,
            (
                product_id,
            )
        )

        affected = cursor.rowcount


        conn.commit()

        conn.close()

        return affected > 0


    except Exception as e:

        conn.rollback()

        conn.close()

        print(
            "DELETE PRODUCT ERROR:",
            e
        )

        return False


# ==========================================
# ค้นหาสินค้าจากชื่อ
# ==========================================

def get_product(category):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT

            id,
            category

        FROM products

        WHERE category=?

        LIMIT 1
        """,
        (
            category,
        )
    )

    row = cursor.fetchone()

    conn.close()

    return row


# ==========================================
# Build 0.86
# แก้ไขราคาแต่ละไซส์
# ==========================================

def update_product_price(price_id, cost, price):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE product_prices

        SET
            cost=?,
            price=?

        WHERE id=?
        """,
        (
            cost,
            price,
            price_id
        )
    )

    conn.commit()

    conn.close()


# ==========================================
# Build 0.86
# ลบราคาเฉพาะไซส์
# ==========================================

def delete_product_price(price_id):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM product_prices

        WHERE id=?
        """,
        (price_id,)
    )

    conn.commit()

    affected = cursor.rowcount

    conn.close()

    return affected > 0


# ==========================================
# แก้ชื่อสินค้า
# ==========================================

def update_product_name(product_id, category):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE products

        SET category=?

        WHERE id=?
        """,
        (
            category,
            product_id
        )
    )

    conn.commit()

    affected = cursor.rowcount

    conn.close()

    return affected > 0