import sqlite3

# ชี้ไปที่ไฟล์ DB เดิมของคุณ
DB_NAME = "data/maxky_pos.db"


def init_db():
    """ตรวจสอบและเพิ่มคอลัมน์ payment_method และ station_name ในตาราง sales อัตโนมัติ"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "ALTER TABLE sales ADD COLUMN payment_method TEXT DEFAULT 'เงินสด'"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE sales ADD COLUMN station_name TEXT DEFAULT 'จุดขายที่ 1'"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute(
            "ALTER TABLE sales ADD COLUMN event_name TEXT DEFAULT ''"
        )
        conn.commit()
    except sqlite3.OperationalError:
        pass

    conn.close()


def get_recent_sales(station_name: str = "จุดขายที่ 1", event_name: str = None):
    init_db()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    station = station_name if station_name else "จุดขายที่ 1"
    clean_event = str(event_name).strip() if event_name else ""

    rows = []

    # 1. ลองค้นหาตามชื่องานและจุดขายก่อน
    if clean_event:
        query = """
            SELECT
                created_at, category, size, price, event_name, payment_method, station_name
            FROM sales
            WHERE (station_name = ? OR station_name IS NULL OR station_name = '')
              AND event_name = ?
            ORDER BY id DESC
            LIMIT 10
        """
        cursor.execute(query, (station, clean_event))
        rows = cursor.fetchall()

    # 2. ถ้าค้นด้วยชื่องานแล้วไม่พบข้อมูล (หรือไม่ได้ใส่ชื่องาน) ให้ดึงรายการขายล่าสุดทั้งหมดของจุดขายนั้นขึ้นมาแสดงทันที
    if not clean_event or not rows:
        query = """
            SELECT
                created_at, category, size, price, event_name, payment_method, station_name
            FROM sales
            WHERE (station_name = ? OR station_name IS NULL OR station_name = '')
            ORDER BY id DESC
            LIMIT 10
        """
        cursor.execute(query, (station,))
        rows = cursor.fetchall()

    conn.close()

    data = []
    for row in rows:
        created_at = row[0]
        category = row[1]
        size = row[2]
        price = row[3]
        row_event = row[4] or ""
        payment_method = row[5] if len(row) > 5 and row[5] else "เงินสด"
        row_station = row[6] if len(row) > 6 and row[6] else "จุดขายที่ 1"

        # แปลงฟอร์แมตวันที่
        try:
            date_part, time_part = created_at.split(" ")
            year, month, day = date_part.split("-")
            hour, minute, second = time_part.split(":")
            display_time = f"{day}/{month}/{year} {hour}:{minute}"
        except Exception:
            display_time = created_at

        data.append(
            {
                "datetime": display_time,
                "category": category,
                "size": size,
                "price": price,
                "event_name": row_event,
                "payment_method": payment_method,
                "station_name": row_station,
            }
        )

    return data