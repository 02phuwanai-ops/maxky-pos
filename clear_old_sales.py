import os
import pymysql
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

def clear_imported_history():
    host = os.getenv("MYSQL_HOST")
    port = int(os.getenv("MYSQL_PORT", 3306))
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    print(f"กำลังเชื่อมต่อฐานข้อมูล Aiven ที่: {host}...")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )

    try:
        with conn.cursor() as cursor:
            # ลบเฉพาะข้อมูลประวัติเก่าที่มาจาก Excel (is_closed = 1)
            # ยอดขายปัจจุบันที่กำลังขาย (is_closed = 0) จะยังคงอยู่ปลอดภัย
            cursor.execute("DELETE FROM sales WHERE is_closed = 1;")
        conn.commit()
        print("✅ เคลียร์ข้อมูลประวัติเก่าสำเร็จ! ตอนนี้ระบบเหลือเฉพาะยอดขายปัจจุบันแล้วครับ")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clear_imported_history()