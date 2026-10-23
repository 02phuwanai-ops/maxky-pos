import os
import pymysql
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

def clear_today_excel_data():
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
            # ลบเฉพาะข้อมูลวันที่ 2026-10-23 ที่เคย Import จาก Excel (is_closed = 1)
            # โดยเก็บยอดขายปัจจุบันของวันนี้ (is_closed = 0) ไว้ตามเดิม
            sql = """
                DELETE FROM sales 
                WHERE is_closed = 1 
                AND DATE(created_at) = '2026-10-23'
            """
            cursor.execute(sql)
        conn.commit()
        print("✅ ลบข้อมูล Excel ของวันที่ 23 สำเร็จเรียบร้อยแล้วครับ!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    clear_today_excel_data()