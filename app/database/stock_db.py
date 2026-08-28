from dbutils.pooled_db import PooledDB
import pymysql

from app.database.db import get_db_connection


def create_stock_table():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
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
    finally:
        conn.close()


def reduce_stock(category, size, qty=1):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE stock
                SET quantity = quantity - %s
                WHERE category = %s AND size = %s AND quantity >= %s
            """, (qty, category, size, qty))
            return cursor.rowcount > 0
    finally:
        conn.close()


def increase_stock(category, size, qty=1):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE stock
                SET quantity = quantity + %s
                WHERE category = %s AND size = %s
            """, (qty, category, size))
            return cursor.rowcount > 0
    finally:
        conn.close()


def get_stock(category, size):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT quantity FROM stock
                WHERE category = %s AND size = %s LIMIT 1
            """, (category, size))
            result = cursor.fetchone()
            if not result:
                return 0
            return int(result["quantity"] if isinstance(result, dict) else result[0])
    finally:
        conn.close()


def get_sizes():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT size FROM stock ORDER BY size
            """)
            rows = cursor.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [row["size"] for row in rows]
            return [row[0] for row in rows]
    finally:
        conn.close()


def get_sizes_by_product(category):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT size FROM stock
                WHERE category = %s AND quantity > 0
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
            """, (category,))
            rows = cursor.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [row["size"] for row in rows]
            return [row[0] for row in rows]
    finally:
        conn.close()


def get_all_stock():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT category, size, quantity FROM stock
                ORDER BY category,
                    CASE size
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
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [(r["category"], r["size"], r["quantity"]) for r in rows]
            return rows
    finally:
        conn.close()


def get_total_stock():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT IFNULL(SUM(quantity), 0) AS total FROM stock
            """)
            row = cursor.fetchone()
            if not row:
                return 0.0
            if isinstance(row, dict):
                return float(row.get("total", 0))
            return float(row[0]) if row else 0.0
    finally:
        conn.close()


def get_low_stock(limit=2):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT category, size, quantity FROM stock
                WHERE quantity <= %s
                ORDER BY quantity ASC
            """, (limit,))
            rows = cursor.fetchall()
            if not rows:
                return []
            if isinstance(rows[0], dict):
                return [(r["category"], r["size"], r["quantity"]) for r in rows]
            return rows
    finally:
        conn.close()


def get_stock_groups():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT category, size, quantity FROM stock
                ORDER BY category,
                    CASE size
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
    finally:
        conn.close()


def create_product_stock(category):
    create_stock_table()
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sizes = ["S", "M", "L", "XL", "2XL", "3XL"]
            for size in sizes:
                cursor.execute("""
                    INSERT IGNORE INTO stock (category, size, quantity)
                    VALUES (%s, %s, 0)
                """, (category, size))
    finally:
        conn.close()


def cleanup_orphan_stock():
    print("🛡️ Cleanup Stock ถูกระงับชั่วคราวเพื่อความปลอดภัยของข้อมูล")
    return 0