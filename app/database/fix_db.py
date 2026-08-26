import pymysql
from app.database.db import get_db_connection

def add_payment_method_column():
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Syntax เพิ่มคอลัมน์ของ MySQL
        cursor.execute("""
            ALTER TABLE recent_sales 
            ADD COLUMN payment_method VARCHAR(100) DEFAULT 'เงินสด';
        """)
        conn.commit()
        print("✅ เพิ่มคอลัมน์ payment_method ใน MySQL เรียบร้อยแล้ว")
    except Exception as e:
        # หากคอลัมน์มีอยู่แล้ว MySQL จะแจ้ง Error Duplicate column
        print(f"⚠️ ไม่สามารถเพิ่มคอลัมน์ได้ (อาจมีคอลัมน์นี้อยู่แล้ว): {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_payment_method_column()