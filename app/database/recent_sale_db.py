import pymysql
from datetime import datetime
from app.database.db import get_db_connection


def init_db():
    """ตรวจสอบและเพิ่มคอลัมน์ในตาราง sales อัตโนมัติ หากยังไม่มี"""
    conn = get_db_connection()
    cursor = conn.cursor()

    columns_to_add = [
        ("payment_method", "VARCHAR(100) DEFAULT 'เงินสด'"),
        ("station_name", "VARCHAR(100) DEFAULT 'จุดขายที่ 1'"),
        ("event_name", "VARCHAR(100) DEFAULT ''")
    ]

    for col_name, col_def in columns_to_add:
        try:
            cursor.execute(f"ALTER TABLE sales ADD COLUMN {col_name} {col_def}")
            conn.commit()
        except Exception:
            # หากคอลัมน์มีอยู่แล้ว MySQL จะข้ามโดยไม่เกิด Error พัง
            pass

    conn.close()


def get_recent_sales(station_name: str = "จุดขายที่ 1", event_name: str = None):
    init_db()

    conn = get_db_connection()
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
            WHERE (station_name = %s OR station_name IS NULL OR station_name = '')
              AND event_name = %s
            ORDER BY id DESC
            LIMIT 10
        """
        cursor.execute(query, (station, clean_event))
        rows = cursor.fetchall()

    # 2. ถ้าค้นด้วยชื่องานแล้วไม่พบข้อมูล ให้ดึงรายการขายล่าสุดทั้งหมดของจุดขายนั้นขึ้นมาแสดงทันที
    if not clean_event or not rows:
        query = """
            SELECT
                created_at, category, size, price, event_name, payment_method, station_name
            FROM sales
            WHERE (station_name = %s OR station_name IS NULL OR station_name = '')
            ORDER BY id DESC
            LIMIT 10
        """
        cursor.execute(query, (station,))
        rows = cursor.fetchall()

    conn.close()

    data = []
    for row in rows:
        # รองรับทั้ง DictCursor และ Normal Tuple
        if isinstance(row, dict):
            created_at = row.get("created_at")
            category = row.get("category")
            size = row.get("size")
            price = float(row.get("price", 0.0)) if row.get("price") is not None else 0.0
            row_event = row.get("event_name") or ""
            payment_method = row.get("payment_method") or "เงินสด"
            row_station = row.get("station_name") or "จุดขายที่ 1"
        else:
            created_at = row[0]
            category = row[1]
            size = row[2]
            price = float(row[3]) if row[3] is not None else 0.0
            row_event = row[4] or ""
            payment_method = row[5] if len(row) > 5 and row[5] else "เงินสด"
            row_station = row[6] if len(row) > 6 and row[6] else "จุดขายที่ 1"

        # แปลงฟอร์แมตวันที่
        if isinstance(created_at, datetime):
            display_time = created_at.strftime("%d/%m/%Y %H:%M")
        else:
            try:
                created_str = str(created_at)
                date_part, time_part = created_str.split(" ")
                year, month, day = date_part.split("-")
                hour, minute = time_part.split(":")[:2]
                display_time = f"{day}/{month}/{year} {hour}:{minute}"
            except Exception:
                display_time = str(created_at)

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