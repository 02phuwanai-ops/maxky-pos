import pymysql
from app.database.db import get_db_connection

products = [
    ("เสื้อยืด", 60, 100),
    ("เสื้อกีฬา", 80, 150),
    ("เสื้อยืดแขนยาว", 100, 180),
    ("เสื้อกีฬาแขนยาว", 120, 220),
    ("เสื้อฟอก", 150, 300),
    ("กางเกง", 70, 150),
]

conn = get_db_connection()
try:
    with conn.cursor() as cursor:
        cursor.executemany(
            """
            INSERT IGNORE INTO products
            (category, cost, price)
            VALUES (%s, %s, %s)
            """,
            products,
        )
    conn.commit()
    print("Product Cost Ready")
finally:
    conn.close()