from app.database.db import get_db_connection

conn = get_db_connection()

try:
    with conn.cursor() as cursor:

        # ดู Index ที่มีอยู่ก่อน
        cursor.execute("SHOW INDEX FROM sales")
        indexes = cursor.fetchall()

        exists = False

        for index in indexes:
            if index["Key_name"] == "idx_sales_recent":
                exists = True
                break

        if exists:
            print("⚠️ idx_sales_recent มีอยู่แล้ว")
        else:
            cursor.execute("""
                CREATE INDEX idx_sales_recent
                ON sales (
                    station_name,
                    is_closed,
                    event_name,
                    id
                )
            """)

            print("✅ สร้าง Index idx_sales_recent สำเร็จ")

finally:
    conn.close()