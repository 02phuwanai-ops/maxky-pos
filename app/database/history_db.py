import pymysql
from app.database.db import get_db_connection


def get_sales_history():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            created_at,
            category,
            size,
            price,
            profit
        FROM sales
        ORDER BY id DESC
        LIMIT 50
        """
    )

    rows = cursor.fetchall()
    conn.close()

    # จัดการแปลงรูปแบบข้อมูลให้คืนค่าเป็น Tuple เหมือนเดิม
    if rows and isinstance(rows[0], dict):
        return [
            (
                r["created_at"],
                r["category"],
                r["size"],
                float(r["price"]) if r["price"] is not None else 0.0,
                float(r["profit"]) if r["profit"] is not None else 0.0
            )
            for r in rows
        ]

    return rows