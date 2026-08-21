import sqlite3

DB_NAME = "data/maxky_pos.db"

items = [

    ("เสื้อยืด","S",10),
    ("เสื้อยืด","M",10),
    ("เสื้อยืด","L",10),
    ("เสื้อยืด","XL",10),
    ("เสื้อยืด","2XL",10),
    ("เสื้อยืด","3XL",10),

    ("เสื้อกีฬา","S",10),
    ("เสื้อกีฬา","M",10),
    ("เสื้อกีฬา","L",10),
    ("เสื้อกีฬา","XL",10),

]

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

for category, size, qty in items:

    cursor.execute(
        """
        SELECT id
        FROM stock
        WHERE category=?
        AND size=?
        """,
        (category, size)
    )

    if cursor.fetchone() is None:

        cursor.execute(
            """
            INSERT INTO stock
            (category,size,quantity)
            VALUES (?,?,?)
            """,
            (category, size, qty)
        )

conn.commit()
conn.close()

print("Stock Ready")