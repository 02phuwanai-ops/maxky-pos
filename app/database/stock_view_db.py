import pymysql
from app.database.db import get_db_connection


# ==========================================
# ดึงข้อมูลสต็อกสินค้าทั้งหมด (ดึงจาก products เป็นหลัก)
# ==========================================
def get_stock_all():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # ใช้ LEFT JOIN เพื่อให้ดึงสินค้าทุกตัวมาแสดง แม้จะยังไม่มีข้อมูลใน stock
            cursor.execute(
                """
                SELECT 
                    p.category,
                    COALESCE(s.size, 'S') AS size,
                    COALESCE(s.quantity, 0) AS quantity
                FROM products p
                LEFT JOIN stock s ON TRIM(p.category) = TRIM(s.category)
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
                """
            )
            data = cursor.fetchall()
            
            # แปลง Dict Cursor ให้เป็น Tuple เพื่อรองรับการ unpack (category, size, qty)
            if data and isinstance(data[0], dict):
                return [(r["category"], r["size"], r["quantity"]) for r in data]
                
        return data
    finally:
        conn.close()


# ==========================================
# ดึงข้อมูลสินค้าที่สต็อกใกล้หมด (<= 5)
# ==========================================
def get_low_stock():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    category,
                    size,
                    quantity
                FROM stock
                WHERE quantity <= 5
                ORDER BY quantity ASC
                """
            )
            data = cursor.fetchall()
            
            if data and isinstance(data[0], dict):
                return [(r["category"], r["size"], r["quantity"]) for r in data]
                
        return data
    finally:
        conn.close()