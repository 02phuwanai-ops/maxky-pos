import pymysql
from app.database.db import get_db_connection

items = [
    ("เสื้อยืด", "S", 10),
    ("เสื้อยืด", "M", 10),
    ("เสื้อยืด", "L", 10),
    ("เสื้อยืด", "XL", 10),
    ("เสื้อยืด", "2XL", 10),
    ("เสื้อยืด", "3XL", 10),

    ("เสื้อกีฬา", "S", 10),
    ("เสื้อกีฬา", "M", 10),
    ("เสื้อกีฬา", "L", 10),
    ("เสื้อกีฬา", "XL", 10),
]

conn = get_db_connection()
try:
    with conn.cursor() as cursor:
        for category, size, qty in items:
            cursor.execute(
                """
                SELECT id
                FROM stock
                WHERE category = %s AND size = %s
                """,
                (category, size)
            )

            if cursor.fetchone() is None:
                cursor.execute(
                    """
                    INSERT INTO stock (category, size, quantity)
                    VALUES (%s, %s, %s)
                    """,
                    (category, size, qty)
                )

    conn.commit()
    print("Stock Ready")
finally:
    conn.close()