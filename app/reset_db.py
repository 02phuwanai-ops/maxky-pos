import os
import sqlite3

files = ['database.db', 'pos.db']

for f in files:
    if os.path.exists(f):
        conn = sqlite3.connect(f)
        cursor = conn.cursor()
        
        # ดึงรายชื่อตารางทั้งหมด
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = cursor.fetchall()
        
        # ลบข้อมูลในทุกตาราง
        for t in tables:
            cursor.execute(f"DELETE FROM {t[0]};")
            
        conn.commit()
        conn.close()
        print(f"Cleared {f} successfully!")

print("RESET_ALL_DONE")