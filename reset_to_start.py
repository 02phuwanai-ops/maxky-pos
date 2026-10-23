import os
import pymysql
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

def reset_database_to_start():
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
            # ลบข้อมูลการขายทั้งหมดในตาราง sales เพื่อเริ่มต้นใหม่ก่อนการ Import Excel
            cursor.execute("DELETE FROM sales;")
            # รีเซ็ตค่า Auto Increment ให้กลับมาเริ่มต้นที่ 1
            cursor.execute("ALTER TABLE sales AUTO_INCREMENT = 1;")
        conn.commit()
        print("✅ รีเซ็ตข้อมูลการขายทั้งหมดกลับสู่จุดเริ่มต้นสำเร็จเรียบร้อยแล้วครับ!")
    except Exception as e:
        print(f"❌ เกิดข้อผิดพลาด: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    reset_database_to_start()