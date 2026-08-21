import sqlite3

# ระบุ path ของไฟล์ .db ของคุณ (เช่น database.db หรือ pos.db)
conn = sqlite3.connect("database.db")
cursor = conn.cursor()

try:
    cursor.execute(
        "ALTER TABLE recent_sales ADD COLUMN payment_method TEXT DEFAULT 'เงินสด';"
    )
    conn.commit()
    print("✅ เพิ่มคอลัมน์ payment_method เรียบร้อยแล้ว")
except Exception as e:
    print(f"❌ เกิดข้อผิดพลาด: {e}")
finally:
    conn.close()