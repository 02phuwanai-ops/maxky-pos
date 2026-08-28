from datetime import datetime
import pymysql

from app.database.db import get_db_connection

# ==========================================
# สร้างตาราง Sales & Shifts ใน MySQL
# ==========================================

def create_sales_table():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(255),
                    size VARCHAR(100),
                    cost DECIMAL(10,2) DEFAULT 0.00,
                    price DECIMAL(10,2) DEFAULT 0.00,
                    profit DECIMAL(10,2) DEFAULT 0.00,
                    created_at DATETIME,
                    event_name VARCHAR(255),
                    payment_method VARCHAR(100) DEFAULT 'เงินสด',
                    station_name VARCHAR(255) DEFAULT 'จุดขายที่ 1',
                    shift_id INT,
                    is_closed INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)
                        # เพิ่ม Index สำหรับคำสั่งที่ POS เรียกบ่อย
            try:
                cursor.execute("""
                    CREATE INDEX idx_sales_station_open_id
                    ON sales (station_name, is_closed, id)
                """)
            except Exception:
                pass

            try:
                cursor.execute("""
                    CREATE INDEX idx_sales_shift_open
                    ON sales (shift_id, is_closed)
                """)
            except Exception:
                pass
    finally:
        conn.close()


def create_shift_table():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
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
    finally:
        conn.close()


def init_db():
    create_sales_table()
    create_shift_table()


# ==========================================
# ฟังก์ชันช่วยเหลือภายใน (Fast Helpers)
# ==========================================

def get_current_shift_fast(cursor, station_name, event_name):
    """หา Shift ปัจจุบันด้วย Cursor เดียวกัน"""

    cursor.execute(
        """
        SELECT id
        FROM shifts
        WHERE station_name = %s
          AND event_name = %s
          AND status = 'OPEN'
        ORDER BY id DESC
        LIMIT 1
        """,
        (station_name, event_name),
    )

    row = cursor.fetchone()

    if row:
        return row["id"]

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        """
        INSERT INTO shifts (
            station_name,
            event_name,
            opened_at,
            status
        )
        VALUES (%s, %s, %s, 'OPEN')
        """,
        (station_name, event_name, now),
    )

    return cursor.lastrowid

def get_current_shift(station_name="จุดขายที่ 1", event_name=""):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            return get_current_shift_fast(cursor, station_name, event_name)
    finally:
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
    station_name="จุดขายที่ 1",
):
    event_name = event_name.strip() if event_name else ""
    cost = float(cost or 0.0)
    price = float(price or 0.0)
    profit = price - cost
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            shift_id = get_current_shift_fast(cursor, station_name, event_name)
            
            # 1. บันทึกการขาย
            cursor.execute(
                """
                INSERT INTO sales (category, size, cost, price, profit, created_at, event_name, payment_method, shift_id, station_name, is_closed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 0)
                """,
                (category, size, cost, price, profit, now_str, event_name, payment_method, shift_id, station_name),
            )
            sale_id = cursor.lastrowid

        conn.commit()
        return sale_id
    except Exception as e:
        conn.rollback()
        print("ADD SALE ERROR:", e)
        return False
    finally:
        conn.close()


# ==========================================
# 🎯 ยกเลิกรายการขายล่าสุด (รองรับ Parameter ทุกรูปแบบ)
# ==========================================

def cancel_last_sale(station_name="จุดขายที่ 1", event_name=""):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # 1. ค้นหาการขายล่าสุดที่ยังไม่ปิดกะ
            cursor.execute(
                """
                SELECT id, category, size 
                FROM sales 
                WHERE station_name = %s AND is_closed = 0 
                ORDER BY id DESC LIMIT 1
                """,
                (station_name,),
            )
            last_sale = cursor.fetchone()

            if not last_sale:
                return False

            if isinstance(last_sale, dict):
                sale_id = last_sale.get("id")
                category = last_sale.get("category")
                size = last_sale.get("size")
            else:
                sale_id = last_sale[0]
                category = last_sale[1]
                size = last_sale[2]

            
            # 3. ลบรายการขาย
            cursor.execute("DELETE FROM sales WHERE id = %s", (sale_id,))

        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("CANCEL LAST SALE ERROR:", e)
        return False
    finally:
        conn.close()


def delete_sale(sale_id=None, station_name="จุดขายที่ 1", event_name=""):
    """ลบรายการขาย โดยไม่จัดการ Stock"""

    if sale_id is not None:
        conn = get_db_connection()

        try:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM sales WHERE id = %s",
                    (sale_id,)
                )

            conn.commit()
            return cursor.rowcount > 0

        except Exception as e:
            conn.rollback()
            print("DELETE SALE ERROR:", e)
            return False

        finally:
            conn.close()

    return cancel_last_sale(station_name, event_name)


# ==========================================
# รายงานและฟังก์ชันอื่นๆ
# ==========================================

def today_sales_count():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) as total FROM sales WHERE DATE(created_at) = %s AND is_closed = 0",
                (today,),
            )
            row = cursor.fetchone()
            return int(row.get("total") or 0) if row else 0
    finally:
        conn.close()


def today_sales_revenue():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COALESCE(SUM(price), 0) as total_rev FROM sales WHERE DATE(created_at) = %s AND is_closed = 0",
                (today,),
            )
            row = cursor.fetchone()
            return float(row.get("total_rev") or 0.0) if row else 0.0
    finally:
        conn.close()


def get_shift_sales_summary(station_name="จุดขายที่ 1", event_name=""):
    station_name = str(station_name).strip() if station_name else "จุดขายที่ 1"
    event_name = str(event_name).strip() if event_name else ""

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            shift_id = get_current_shift_fast(cursor, station_name, event_name)
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_items,
                    COALESCE(SUM(price), 0) as total_revenue,
                    COALESCE(SUM(profit), 0) as total_profit,
                    COALESCE(SUM(CASE WHEN payment_method = 'เงินสด' THEN price ELSE 0 END), 0) as cash,
                    COALESCE(SUM(CASE WHEN payment_method = 'โอนเงิน' THEN price ELSE 0 END), 0) as transfer,
                    COALESCE(SUM(CASE WHEN payment_method = 'คนละครึ่ง' THEN price ELSE 0 END), 0) as half
                FROM sales
                WHERE shift_id = %s AND is_closed = 0
            """,
                (shift_id,),
            )
            summary = cursor.fetchone() or {}

            return {
                "shift_id": shift_id,
                "station_name": station_name,
                "event_name": event_name,
                "total_items": int(summary.get("total_items") or 0),
                "total_revenue": float(summary.get("total_revenue") or 0.0),
                "total_profit": float(summary.get("total_profit") or 0.0),
                "cash": float(summary.get("cash") or 0.0),
                "transfer": float(summary.get("transfer") or 0.0),
                "half": float(summary.get("half") or 0.0),
            }
    finally:
        conn.close()


def get_recent_sales(station_name: str = "จุดขายที่ 1", event_name: str = None):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            query = """
                SELECT created_at, category, size, price, event_name, payment_method, station_name 
                FROM sales
                WHERE is_closed = 0
            """
            params = []
            if station_name:
                query += " AND station_name = %s"
                params.append(station_name)

            if event_name:
                query += " AND event_name = %s"
                params.append(event_name)

            query += " ORDER BY id DESC LIMIT 10"
            cursor.execute(query, tuple(params) if params else ())
            rows = cursor.fetchall()
            data = []
            for row in rows:
                created_at = row.get("created_at") if isinstance(row, dict) else row[0]
                category = row.get("category") if isinstance(row, dict) else row[1]
                size = row.get("size") if isinstance(row, dict) else row[2]
                price = row.get("price") if isinstance(row, dict) else row[3]
                ev_name = row.get("event_name") if isinstance(row, dict) else row[4]
                pay_method = row.get("payment_method") if isinstance(row, dict) else row[5]
                st_name = row.get("station_name") if isinstance(row, dict) else row[6]

                display_time = (
                    created_at.strftime("%d/%m/%Y %H:%M")
                    if isinstance(created_at, datetime)
                    else str(created_at or "-")
                )
                data.append({
                    "datetime": display_time,
                    "category": category,
                    "size": size,
                    "price": float(price or 0.0),
                    "event_name": ev_name or "",
                    "payment_method": pay_method or "เงินสด",
                    "station_name": st_name or "จุดขายที่ 1",
                })
            return data
    finally:
        conn.close()


def close_current_shift(station_name="จุดขายที่ 1", event_name=""):
    event_name = event_name.strip() if event_name else ""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            # หา Shift จาก Connection เดียวกัน
            cursor.execute(
                """
                SELECT id
                FROM shifts
                WHERE station_name = %s
                  AND event_name = %s
                  AND status = 'OPEN'
                ORDER BY id DESC
                LIMIT 1
                """,
                (station_name, event_name),
            )

            shift = cursor.fetchone()

            if not shift:
                return {
                    "total_items": 0,
                    "total_revenue": 0.0,
                    "total_profit": 0.0,
                    "cash": 0.0,
                    "transfer": 0.0,
                    "half": 0.0,
                }

            shift_id = shift["id"]

            # สรุปยอดด้วย Cursor เดียวกัน
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_items,
                    COALESCE(SUM(price), 0) AS total_revenue,
                    COALESCE(SUM(profit), 0) AS total_profit,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_method = 'เงินสด'
                                THEN price
                                ELSE 0
                            END
                        ), 0
                    ) AS cash,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_method = 'โอนเงิน'
                                THEN price
                                ELSE 0
                            END
                        ), 0
                    ) AS transfer,
                    COALESCE(
                        SUM(
                            CASE
                                WHEN payment_method = 'คนละครึ่ง'
                                THEN price
                                ELSE 0
                            END
                        ), 0
                    ) AS half
                FROM sales
                WHERE shift_id = %s
                  AND is_closed = 0
                """,
                (shift_id,),
            )

            summary = cursor.fetchone() or {}

            result = {
                "shift_id": shift_id,
                "station_name": station_name,
                "event_name": event_name,
                "total_items": int(summary.get("total_items") or 0),
                "total_revenue": float(summary.get("total_revenue") or 0.0),
                "total_profit": float(summary.get("total_profit") or 0.0),
                "cash": float(summary.get("cash") or 0.0),
                "transfer": float(summary.get("transfer") or 0.0),
                "half": float(summary.get("half") or 0.0),
            }

            # ปิด Shift
            cursor.execute(
                """
                UPDATE shifts
                SET status = 'CLOSED',
                    closed_at = %s
                WHERE id = %s
                """,
                (now, shift_id),
            )

            # ปิดรายการขายทั้งหมดของ Shift
            cursor.execute(
                """
                UPDATE sales
                SET is_closed = 1
                WHERE shift_id = %s
                """,
                (shift_id,),
            )

            # เปิด Shift ใหม่
            cursor.execute(
                """
                INSERT INTO shifts (
                    station_name,
                    event_name,
                    status,
                    opened_at
                )
                VALUES (%s, %s, 'OPEN', %s)
                """,
                (station_name, event_name, now),
            )

        conn.commit()
        return result

    except Exception as e:
        conn.rollback()
        print("CLOSE SHIFT ERROR:", e)
        raise

    finally:
        conn.close()


def get_last_sale(station_name="จุดขายที่ 1", event_name=""):
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT id, category, size FROM sales WHERE station_name = %s AND is_closed = 0 ORDER BY id DESC LIMIT 1",
                (station_name,),
            )
            return cursor.fetchone()
    finally:
        conn.close()


def get_event_names():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT DISTINCT event_name FROM sales WHERE event_name IS NOT NULL AND TRIM(event_name) != '' ORDER BY event_name"
            )
            rows = cursor.fetchall()
            return [row.get("event_name") if isinstance(row, dict) else row[0] for row in rows]
    finally:
        conn.close()