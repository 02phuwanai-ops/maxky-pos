import pymysql
from datetime import datetime
from app.database.db import get_db_connection


# ==========================================
# สร้างตาราง Sales & Shifts ใน MySQL
# ==========================================

def create_sales_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(255),
            size VARCHAR(100),
            cost DECIMAL(10,2),
            price DECIMAL(10,2),
            profit DECIMAL(10,2),
            created_at DATETIME,
            event_name VARCHAR(255),
            payment_method VARCHAR(100) DEFAULT 'เงินสด',
            station_name VARCHAR(255) DEFAULT 'จุดขายที่ 1',
            shift_id INT,
            is_closed INT DEFAULT 0
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()


# ==========================================
# เพิ่มรายการขาย
# ==========================================

def add_sale(
    category,
    size,
    cost,
    price,
    event_name="",
    payment_method="เงินสด",
    station_name="จุดขายที่ 1"
):
    event_name = event_name.strip() if event_name else ""
    profit = price - cost
    
    # ดึง shift_id ของกะปัจจุบัน (แยกตาม จุดขาย + ชื่องาน)
    shift_id = get_current_shift(station_name, event_name)

    conn = get_db_connection()
    cursor = conn.cursor()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO sales
        (
            category,
            size,
            cost,
            price,
            profit,
            created_at,
            event_name,
            payment_method,
            shift_id,
            station_name,
            is_closed
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
        """,
        (
            category,
            size,
            cost,
            price,
            profit,
            now_str,
            event_name,
            payment_method,
            shift_id,
            station_name
        )
    )

    sale_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return sale_id


# ==========================================
# จำนวนรายการขายวันนี้
# ==========================================

def today_sales_count():
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sales
        WHERE DATE(created_at) = %s AND is_closed = 0
        """,
        (today,)
    )

    row = cursor.fetchone()
    result = row[0] if row and row[0] is not None else 0

    conn.close()

    return result


# ==========================================
# รายได้วันนี้
# ==========================================

def today_sales_revenue():
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
        SELECT COALESCE(SUM(price), 0)
        FROM sales
        WHERE DATE(created_at) = %s AND is_closed = 0
        """,
        (today,)
    )

    row = cursor.fetchone()
    result = float(row[0]) if row and row[0] is not None else 0.0

    conn.close()

    return result


# ==========================================
# ข้อมูลรายการขายล่าสุด (ของงานและจุดขายปัจจุบัน)
# ==========================================

def get_last_sale(station_name="จุดขายที่ 1", event_name=""):
    event_name = event_name.strip() if event_name else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category,
            size
        FROM sales
        WHERE station_name = %s AND is_closed = 0
        ORDER BY id DESC
        LIMIT 1
        """,
        (station_name,)
    )

    row = cursor.fetchone()
    conn.close()

    return row


# ==========================================
# ลบ Sale ตาม ID
# ==========================================

def delete_sale(sale_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM sales
        WHERE id = %s
        """,
        (sale_id,)
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted > 0


# ==========================================
# DEBUG
# ==========================================

def get_sales_debug():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT
            id,
            category,
            size,
            cost,
            price,
            profit,
            created_at
        FROM sales
        ORDER BY id DESC
        LIMIT 10
        """
    )

    rows = cursor.fetchall()
    conn.close()

    return rows


# ==========================================
# รายชื่อชื่องานทั้งหมด
# ==========================================

def get_event_names():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT
            event_name
        FROM sales
        WHERE
            event_name IS NOT NULL
        AND
            TRIM(event_name) != ''
        ORDER BY event_name
    """)

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


def init_db():
    """ตรวจสอบและสร้างตาราง sales และ shifts อัตโนมัติ"""
    create_sales_table()
    create_shift_table()


# ==========================================
# ดึงรายการขายล่าสุด (แยกตามจุดขาย + ชื่องาน)
# ==========================================

def get_recent_sales(station_name: str = "จุดขายที่ 1", event_name: str = None):
    init_db()

    conn = get_db_connection()
    cursor = conn.cursor()

    conditions = ["station_name = %s", "is_closed = 0"]
    params = [station_name]

    if event_name and event_name.strip():
        conditions.append("event_name = %s")
        params.append(event_name.strip())

    where_clause = " WHERE " + " AND ".join(conditions)

    query = f"""
        SELECT
            created_at,
            category,
            size,
            price,
            event_name,
            payment_method,
            station_name
        FROM sales
        {where_clause}
        ORDER BY id DESC
        LIMIT 5
    """

    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()

    data = []
    for row in rows:
        created_at = row[0]
        category = row[1]
        size = row[2]
        price = float(row[3]) if row[3] is not None else 0.0
        row_event = row[4]
        payment_method = row[5] if len(row) > 5 and row[5] else "เงินสด"
        row_station = row[6] if len(row) > 6 and row[6] else "จุดขายที่ 1"

        if isinstance(created_at, datetime):
            display_time = created_at.strftime("%d/%m/%Y %H:%M")
        else:
            try:
                created_str = str(created_at)
                date_part, time_part = created_str.split(" ")
                year, month, day = date_part.split("-")
                hour, minute, second = time_part.split(":")
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


# ==========================================
# ระบบ SHIFTS & STATIONS
# ==========================================

def create_shift_table():
    """สร้างตาราง shifts สำหรับเก็บรอบการขาย"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            station_name VARCHAR(255) DEFAULT 'จุดขายที่ 1',
            event_name VARCHAR(255) DEFAULT '',
            opened_at DATETIME,
            closed_at DATETIME,
            status VARCHAR(50) DEFAULT 'OPEN'
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """)

    conn.commit()
    conn.close()


def get_current_shift(station_name="จุดขายที่ 1", event_name=""):
    """ดึง shift_id ที่เปิดใช้งานอยู่ของจุดขายและชื่องานนั้นๆ (ถ้ายังไม่มีจะเปิดให้อัตโนมัติ)"""
    create_shift_table()
    event_name = event_name.strip() if event_name else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM shifts 
        WHERE station_name = %s AND event_name = %s AND status = 'OPEN' 
        ORDER BY id DESC LIMIT 1
    """, (station_name, event_name))

    row = cursor.fetchone()

    if row:
        shift_id = row[0]
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO shifts (station_name, event_name, opened_at, status)
            VALUES (%s, %s, %s, 'OPEN')
        """, (station_name, event_name, now))
        conn.commit()
        shift_id = cursor.lastrowid

    conn.close()
    return shift_id


def get_shift_sales_summary(station_name="จุดขายที่ 1", event_name=""):
    """คำนวณสรุปยอดขายเฉพาะ Shift ที่ OPEN และตรงกับจุดขาย + ชื่องานเท่านั้น"""
    event_name = event_name.strip() if event_name else ""
    shift_id = get_current_shift(station_name, event_name)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_items,
            COALESCE(SUM(price), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN payment_method = 'เงินสด' THEN price ELSE 0 END), 0) as cash,
            COALESCE(SUM(CASE WHEN payment_method = 'โอนเงิน' THEN price ELSE 0 END), 0) as transfer,
            COALESCE(SUM(CASE WHEN payment_method = 'คนละครึ่ง' THEN price ELSE 0 END), 0) as half
        FROM sales
        WHERE station_name = %s AND event_name = %s AND shift_id = %s AND is_closed = 0
    """, (station_name, event_name, shift_id))

    summary = cursor.fetchone()
    conn.close()

    return {
        "shift_id": shift_id,
        "station_name": station_name,
        "event_name": event_name,
        "total_items": summary[0] if summary else 0,
        "total_revenue": float(summary[1]) if summary and summary[1] is not None else 0.0,
        "cash": float(summary[2]) if summary and summary[2] is not None else 0.0,
        "transfer": float(summary[3]) if summary and summary[3] is not None else 0.0,
        "half": float(summary[4]) if summary and summary[4] is not None else 0.0
    }


def close_current_shift(station_name="จุดขายที่ 1", event_name=""):
    """ปิดรอบการขายเฉพาะจุดขายและชื่องานที่สั่งเท่านั้น"""
    event_name = event_name.strip() if event_name else ""
    summary = get_shift_sales_summary(station_name, event_name)
    shift_id = summary.get("shift_id")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"🛠️ [DB EXECUTING UPDATE] shift_id={shift_id} | station='{station_name}' | event='{event_name}'")

    if not shift_id:
        print("⚠️ ไม่พบ shift_id ที่เปิดอยู่ ยกเลิกการปิดยอด")
        return summary

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. ปิด Shift
    cursor.execute("""
        UPDATE shifts 
        SET status = 'CLOSED', closed_at = %s 
        WHERE id = %s AND station_name = %s AND event_name = %s
    """, (now, shift_id, station_name, event_name))
    print(f"   └─ แถวที่โดนปิดในตาราง 'shifts': {cursor.rowcount} รายการ")

    # 2. ปิดรายการขาย
    cursor.execute("""
        UPDATE sales 
        SET is_closed = 1 
        WHERE station_name = %s AND event_name = %s AND shift_id = %s
    """, (station_name, event_name, shift_id))
    print(f"   └─ แถวที่โดนปิดในตาราง 'sales': {cursor.rowcount} รายการ")

    # 3. เปิด Shift ใหม่
    cursor.execute("""
        INSERT INTO shifts (station_name, event_name, status, opened_at)
        VALUES (%s, %s, 'OPEN', %s)
    """, (station_name, event_name, now))

    conn.commit()
    conn.close()

    return summary