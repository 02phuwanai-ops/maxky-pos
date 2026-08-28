import app.database.db as db

print("📄 Python กำลังใช้ไฟล์:")
print(db.__file__)

print("\n📋 ตัวแปรที่มี:")
print([name for name in dir(db) if not name.startswith("__")])

print("\n📄 เนื้อหา db.py ที่ Python อ่านจากดิสก์:")
print("-" * 50)

with open(db.__file__, "r", encoding="utf-8") as f:
    print(f.read())

print("-" * 50)