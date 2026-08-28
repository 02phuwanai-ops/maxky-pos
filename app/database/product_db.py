import os
import pymysql
from dotenv import load_dotenv, find_dotenv
from app.database.db import get_db_connection

# 🟢 บังคับโหลดไฟล์ .env
load_dotenv(find_dotenv(usecwd=True), override=True)

# ==========================================
# Product Table
# ==========================================

def create_product_table():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
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
    finally:
        conn.close()


# ==========================================
# เพิ่มสินค้า
# ==========================================

def add_product(category):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO products(category)
                VALUES(%s)
            """, (category,))
            return cursor.lastrowid
    finally:
        conn.close()


# ==========================================
# เพิ่มราคาแต่ละไซส์
# ==========================================

def add_product_price(product_id, size, cost, price):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO product_prices(
                    product_id,
                    size,
                    cost,
                    price
                )
                VALUES(%s, %s, %s, %s)
            """, (product_id, size, cost, price))
    finally:
        conn.close()


# ==========================================
# รายชื่อสินค้า
# ==========================================

def get_products():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, category
                FROM products
                ORDER BY category
            """)
            rows = cursor.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [(r["id"], r["category"]) for r in rows]
            return rows
    finally:
        conn.close()


# ==========================================
# ราคาทั้งหมดของสินค้า
# ==========================================

def get_product_sizes(product_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
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
            """, (product_id,))
            rows = cursor.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [(r["id"], r["size"], float(r["cost"]), float(r["price"])) for r in rows]
            return rows
    finally:
        conn.close()


# ==========================================
# ใช้ตอนขาย (ราคาแยกตามสินค้า + ไซส์)
# ==========================================

def get_product_price(category, size):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
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
            """, (category, size))
            row = cursor.fetchone()
            if not row:
                return None
            if isinstance(row, dict):
                return (float(row.get("cost", 0)), float(row.get("price", 0)))
            return row
    finally:
        conn.close()


# ==========================================
# แก้ไขราคาแต่ละไซส์
# ==========================================

def update_product_price(price_id, cost, price):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE product_prices
                SET
                    cost = %s,
                    price = %s
                WHERE id = %s
            """, (cost, price, price_id))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ==========================================
# ลบราคาไซส์
# ==========================================

def delete_product_price(price_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM product_prices
                WHERE id = %s
            """, (price_id,))
            return cursor.rowcount > 0
    finally:
        conn.close()


# ==========================================
# ลบสินค้า (พร้อมลบ Stock และราคา)
# ==========================================

def delete_product(product_id):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. หา category ก่อนลบ
            cursor.execute("""
                SELECT category
                FROM products
                WHERE id = %s
                LIMIT 1
            """, (product_id,))
            row = cursor.fetchone()

            if not row:
                return False

            category = row.get("category") if isinstance(row, dict) else row[0]

            # 2. ลบ Stock ของสินค้า
            cursor.execute("""
                DELETE FROM stock
                WHERE TRIM(category) = TRIM(%s)
            """, (category,))

            # 3. ลบราคาของสินค้า
            cursor.execute("""
                DELETE FROM product_prices
                WHERE product_id = %s
            """, (product_id,))

            # 4. ลบสินค้า
            cursor.execute("""
                DELETE FROM products
                WHERE id = %s
            """, (product_id,))

            return cursor.rowcount > 0
    except Exception as e:
        print("DELETE PRODUCT ERROR:", e)
        return False
    finally:
        conn.close()


# ==========================================
# ค้นหาสินค้าจากชื่อ
# ==========================================

def get_product(category):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    id,
                    category
                FROM products
                WHERE category = %s
                LIMIT 1
            """, (category,))
            row = cursor.fetchone()
            if not row:
                return None
            if isinstance(row, dict):
                return (row["id"], row["category"])
            return row
    finally:
        conn.close()


# ==========================================
# แก้ชื่อสินค้า
# ==========================================

def update_product_name(product_id, category):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE products
                SET category = %s
                WHERE id = %s
            """, (category, product_id))
            return cursor.rowcount > 0
    finally:
        conn.close()

def get_sale_products():
    """
    ดึงสินค้า + ไซส์ที่มีสต็อก + ราคา
    สำหรับหน้า /sale โดยใช้ SQL เพียง 1 Query
    """
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    p.id AS product_id,
                    p.category,
                    s.size,
                    s.quantity,
                    pp.cost,
                    pp.price
                FROM products p
                INNER JOIN stock s
                    ON s.category = p.category
                INNER JOIN product_prices pp
                    ON pp.product_id = p.id
                   AND pp.size = s.size
                WHERE s.quantity > 0
                ORDER BY
                    p.category,
                    CASE s.size
                        WHEN 'S' THEN 1
                        WHEN 'M' THEN 2
                        WHEN 'L' THEN 3
                        WHEN 'XL' THEN 4
                        WHEN '2XL' THEN 5
                        WHEN '3XL' THEN 6
                        ELSE 99
                    END
            """)

            rows = cursor.fetchall()

            products = {}

            for row in rows:
                product_id = row["product_id"]
                category = row["category"]

                if category not in products:
                    products[category] = {
                        "id": product_id,
                        "name": category,
                        "sizes": [],
                        "price": float(row["price"] or 0)
                    }

                products[category]["sizes"].append(row["size"])

            return list(products.values())

    finally:
        conn.close()