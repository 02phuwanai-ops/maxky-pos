import sqlite3
from datetime import datetime

DB_NAME = "data/maxky_pos.db"


# ==========================================
# สร้างตาราง Sales
# ==========================================

def create_sales_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            size TEXT,
            cost REAL,
            price REAL,
            profit REAL,
            created_at TEXT,
            event_name TEXT,
            payment_method TEXT DEFAULT 'เงินสด',
            station_name TEXT DEFAULT 'จุดขายที่ 1',
            shift_id INTEGER,
            is_closed INTEGER DEFAULT 0
        )
    """)

    # --------------------------------------
    # ตรวจสอบฐานข้อมูลเก่า
    # --------------------------------------
    cursor.execute("""
        PRAGMA table_info(sales)
    """)

    columns = [row[1] for row in cursor.fetchall()]

    if "event_name" not in columns:
        cursor.execute("""
            ALTER TABLE sales
            ADD COLUMN event_name TEXT
        """)

    if "payment_method" not in columns:
        cursor.execute("""
            ALTER TABLE sales
            ADD COLUMN payment_method TEXT DEFAULT 'เงินสด'
        """)

    if "station_name" not in columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN station_name TEXT DEFAULT 'จุดขายที่ 1'")
    if "shift_id" not in columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN shift_id INTEGER")
    if "is_closed" not in columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN is_closed INTEGER DEFAULT 0")

    conn.commit()
    conn.close()


# ==========================================
# เพิ่มรายการขาย (แก้ไขให้บันทึก payment_method ลง DB)
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

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

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
        VALUES (?,?,?,?,?,?,?,?,?,?,0)
        """,
        (
            category,
            size,
            cost,
            price,
            profit,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
        SELECT COUNT(*)
        FROM sales
        WHERE (DATE(created_at) = DATE(?) OR created_at LIKE ?) AND is_closed = 0
        """,
        (
            today,
            today + "%"
        )
    )

    result = cursor.fetchone()[0] or 0

    conn.close()

    return result


# ==========================================
# รายได้วันนี้
# ==========================================

def today_sales_revenue():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")

    cursor.execute(
        """
        SELECT COALESCE(SUM(price), 0)
        FROM sales
        WHERE (DATE(created_at) = DATE(?) OR created_at LIKE ?) AND is_closed = 0
        """,
        (
            today,
            today + "%"
        )
    )

    result = cursor.fetchone()[0] or 0

    conn.close()

    return result


# ==========================================
# ข้อมูลรายการขายล่าสุด (ของงานและจุดขายปัจจุบัน)
# ==========================================

def get_last_sale(station_name="จุดขายที่ 1", event_name=""):
    event_name = event_name.strip() if event_name else ""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 💡 ปรับปรุง SQL: ดึงรายการขายล่าสุดของ station นี้ ที่ยังไม่ปิดยอด (is_closed = 0)
    # ตัดเงื่อนไข shift_id ออก เพื่อป้องกันปัญหา Shift ID ไม่ตรงกัน
    cursor.execute(
        """
        SELECT
            id,
            category,
            size
        FROM sales
        WHERE station_name = ? AND is_closed = 0
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
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM sales
        WHERE id = ?
        """,
        (
            sale_id,
        )
    )

    deleted = cursor.rowcount

    conn.commit()
    conn.close()

    return deleted > 0


# ==========================================
# DEBUG
# ==========================================

def get_sales_debug():
    conn = sqlite3.connect(DB_NAME)
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
# เพิ่มช่องชื่องานใน Sales
# ==========================================

def add_event_name_column():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        PRAGMA table_info(sales)
    """)

    columns = [row[1] for row in cursor.fetchall()]

    if "event_name" not in columns:
        cursor.execute("""
            ALTER TABLE sales
            ADD COLUMN event_name TEXT
        """)
        conn.commit()

    conn.close()


# ==========================================
# รายชื่อชื่องานทั้งหมด
# ==========================================

def get_event_names():
    conn = sqlite3.connect(DB_NAME)
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
    """ตรวจสอบและเพิ่มคอลัมน์ใหม่ๆ ในตาราง sales อัตโนมัติ โดยไม่กระทบข้อมูลเดิม"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    create_sales_table()
    create_shift_table()

    cursor.execute("PRAGMA table_info(sales)")
    columns = [row[1] for row in cursor.fetchall()]

    if "payment_method" not in columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN payment_method TEXT DEFAULT 'เงินสด'")
    if "shift_id" not in columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN shift_id INTEGER")
    if "station_name" not in columns:
        cursor.execute("ALTER TABLE sales ADD COLUMN station_name TEXT DEFAULT 'จุดขายที่ 1'")

    conn.commit()
    conn.close()


# ==========================================
# ดึงรายการขายล่าสุด (แก้ไขให้แยกตามจุดขาย + ชื่องาน)
# ==========================================

def get_recent_sales(station_name: str = "จุดขายที่ 1", event_name: str = None):
    init_db()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # สร้างเงื่อนไขการค้นหา
    conditions = ["station_name = ?", "is_closed = 0"]
    params = [station_name]

    # ถ้ามีการระบุชื่องาน ให้เพิ่มเงื่อนไข event_name เข้าไปด้วย
    if event_name and event_name.strip():
        conditions.append("event_name = ?")
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
        price = row[3]
        row_event = row[4]
        payment_method = row[5] if len(row) > 5 and row[5] else "เงินสด"
        row_station = row[6] if len(row) > 6 and row[6] else "จุดขายที่ 1"

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


# ==========================================
# 🆕 ระบบ SHIFTS & STATIONS (ปรับแก้ไขให้ล็อก event_name ร่วมด้วย)
# ==========================================

def create_shift_table():
    """สร้างตาราง shifts สำหรับเก็บรอบการขาย"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS shifts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            station_name TEXT DEFAULT 'จุดขายที่ 1',
            event_name TEXT DEFAULT '',
            opened_at TEXT,
            closed_at TEXT,
            status TEXT DEFAULT 'OPEN'
        )
    """)

    cursor.execute("PRAGMA table_info(shifts)")
    columns = [row[1] for row in cursor.fetchall()]
    if "event_name" not in columns:
        cursor.execute("ALTER TABLE shifts ADD COLUMN event_name TEXT DEFAULT ''")

    conn.commit()
    conn.close()


def get_current_shift(station_name="จุดขายที่ 1", event_name=""):
    """ดึง shift_id ที่เปิดใช้งานอยู่ของจุดขายและชื่องานนั้นๆ (ถ้ายังไม่มีจะเปิดให้อัตโนมัติ)"""
    create_shift_table()
    event_name = event_name.strip() if event_name else ""

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id FROM shifts 
        WHERE station_name = ? AND event_name = ? AND status = 'OPEN' 
        ORDER BY id DESC LIMIT 1
    """, (station_name, event_name))

    row = cursor.fetchone()

    if row:
        shift_id = row[0]
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO shifts (station_name, event_name, opened_at, status)
            VALUES (?, ?, ?, 'OPEN')
        """, (station_name, event_name, now))
        conn.commit()
        shift_id = cursor.lastrowid

    conn.close()
    return shift_id


def get_shift_sales_summary(station_name="จุดขายที่ 1", event_name=""):
    """คำนวณสรุปยอดขายเฉพาะ Shift ที่ OPEN และตรงกับจุดขาย + ชื่องานเท่านั้น"""
    event_name = event_name.strip() if event_name else ""
    shift_id = get_current_shift(station_name, event_name)

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            COUNT(*) as total_items,
            COALESCE(SUM(price), 0) as total_revenue,
            COALESCE(SUM(CASE WHEN payment_method = 'เงินสด' THEN price ELSE 0 END), 0) as cash,
            COALESCE(SUM(CASE WHEN payment_method = 'โอนเงิน' THEN price ELSE 0 END), 0) as transfer,
            COALESCE(SUM(CASE WHEN payment_method = 'คนละครึ่ง' THEN price ELSE 0 END), 0) as half
        FROM sales
        WHERE station_name = ? AND event_name = ? AND shift_id = ? AND is_closed = 0
    """, (station_name, event_name, shift_id))

    summary = cursor.fetchone()
    conn.close()

    return {
        "shift_id": shift_id,
        "station_name": station_name,
        "event_name": event_name,
        "total_items": summary[0] if summary else 0,
        "total_revenue": summary[1] if summary else 0.0,
        "cash": summary[2] if summary else 0.0,
        "transfer": summary[3] if summary else 0.0,
        "half": summary[4] if summary else 0.0
    }


def close_current_shift(station_name="จุดขายที่ 1", event_name=""):
    """ปิดรอบการขายเฉพาะจุดขายและชื่องานที่สั่งเท่านั้น"""
    event_name = event_name.strip() if event_name else ""
    summary = get_shift_sales_summary(station_name, event_name)
    shift_id = summary.get("shift_id")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 🔍 พิมพ์ดูค่าที่ระบบกำลังจะไปสั่งอัปเดตในฐานข้อมูล
    print(f"🛠️ [DB EXECUTING UPDATE] shift_id={shift_id} | station='{station_name}' | event='{event_name}'")

    if not shift_id:
        print("⚠️ ไม่พบ shift_id ที่เปิดอยู่ ยกเลิกการปิดยอด")
        return summary

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. ปิด Shift
    cursor.execute("""
        UPDATE shifts 
        SET status = 'CLOSED', closed_at = ? 
        WHERE id = ? AND station_name = ? AND event_name = ?
    """, (now, shift_id, station_name, event_name))
    print(f"   └─ แถวที่โดนปิดในตาราง 'shifts': {cursor.rowcount} รายการ")

    # 2. ปิดรายการขาย
    cursor.execute("""
        UPDATE sales 
        SET is_closed = 1 
        WHERE station_name = ? AND event_name = ? AND shift_id = ?
    """, (station_name, event_name, shift_id))
    print(f"   └─ แถวที่โดนปิดในตาราง 'sales': {cursor.rowcount} รายการ")

    # 3. เปิด Shift ใหม่
    cursor.execute("""
        INSERT INTO shifts (station_name, event_name, status, opened_at)
        VALUES (?, ?, 'OPEN', ?)
    """, (station_name, event_name, now))

    conn.commit()
    conn.close()

    return summary