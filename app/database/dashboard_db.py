import os
from dbutils.pooled_db import PooledDB
import pymysql
from dotenv import load_dotenv, find_dotenv


# ==========================================
# โหลดไฟล์ .env
# ==========================================

load_dotenv(
    find_dotenv(usecwd=True),
    override=True
)


# ==========================================
# อ่านค่าจาก .env
# ==========================================

DB_HOST = os.getenv("MYSQL_HOST")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_NAME = os.getenv("MYSQL_DATABASE")


# ==========================================
# ตรวจสอบค่าเบื้องต้น
# ==========================================

if not DB_HOST:
    raise RuntimeError("❌ ไม่พบ MYSQL_HOST ในไฟล์ .env")

if not DB_USER:
    raise RuntimeError("❌ ไม่พบ MYSQL_USER ในไฟล์ .env")

if not DB_PASSWORD:
    raise RuntimeError("❌ ไม่พบ MYSQL_PASSWORD ในไฟล์ .env")


# ==========================================
# MySQL Connection Pool
# ==========================================

DB_POOL = PooledDB(
    creator=pymysql,

    maxconnections=20,
    mincached=3,
    maxcached=10,

    blocking=True,

    # ไม่ Ping ทุกครั้งที่ขอ Connection
    # ลด 1 รอบ Network สำหรับทุก Database Request
    ping=0,

    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,

    autocommit=True,

    cursorclass=pymysql.cursors.DictCursor
)

# ==========================================
# ขอ Connection จาก Pool
# ==========================================

def get_db_connection():
    return DB_POOL.connection()


# ==========================================
# รองรับโค้ดเดิมที่เรียก DatabaseManager
# ==========================================

class DatabaseManager:

    @classmethod
    def initialize(cls):
        """ตรวจสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            conn = get_db_connection()

            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 AS test")
                result = cursor.fetchone()

            conn.close()

            print("✅ [MySQL] Successfully connected to Database.")
            return result

        except Exception as e:
            print(f"❌ [MySQL] Connection Failed: {e}")
            raise

    @classmethod
    def connect(cls):
        """รองรับโค้ดเดิมที่เรียก DatabaseManager.connect()"""
        return get_db_connection()


# ==========================================
# สร้างตาราง POS
# ==========================================

def init_pos_db():
    """สร้างตารางสำหรับฝั่ง POS หากยังไม่มีใน MySQL"""

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(100) NOT NULL,
                    size VARCHAR(50) NOT NULL,
                    quantity INT DEFAULT 0,
                    price DECIMAL(10,2) DEFAULT 0.00,
                    cost DECIMAL(10,2) DEFAULT 0.00
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sales (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    category VARCHAR(100) NOT NULL,
                    size VARCHAR(50) NOT NULL,
                    cost DECIMAL(10,2) DEFAULT 0.00,
                    price DECIMAL(10,2) NOT NULL,
                    profit DECIMAL(10,2) NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_name VARCHAR(100) DEFAULT '',
                    payment_method VARCHAR(100) DEFAULT 'เงินสด',
                    station_name VARCHAR(100) DEFAULT 'จุดขายที่ 1',
                    shift_id INT,
                    is_closed INT DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """)

            try:
                cursor.execute(
                    "ALTER TABLE sales ADD COLUMN is_closed INT DEFAULT 0;"
                )
            except Exception:
                pass

    finally:
        conn.close()


# ==========================================
# Dashboard
# ==========================================

def get_dashboard(station_name=None, event_name=None):
    """ดึงยอดขาย จำนวนชิ้น และกำไรเฉพาะรายการที่ยังไม่ปิดกะ"""

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            query = """
                SELECT
                    COUNT(*) AS cnt,
                    IFNULL(SUM(price), 0) AS revenue,
                    IFNULL(SUM(profit), 0) AS profit
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

            try:
                cursor.execute(query, tuple(params))

            except pymysql.err.OperationalError as e:

                if e.args[0] == 1054:

                    cursor.execute(
                        "ALTER TABLE sales ADD COLUMN is_closed INT DEFAULT 0;"
                    )

                    cursor.execute(query, tuple(params))

                else:
                    raise e

            data = cursor.fetchone()

        if data:

            cnt = data.get("cnt", 0)
            revenue = data.get("revenue", 0.0)
            profit = data.get("profit", 0.0)

        else:

            cnt = 0
            revenue = 0.0
            profit = 0.0

        return (
            int(cnt),
            float(revenue) if revenue is not None else 0.0,
            float(profit) if profit is not None else 0.0
        )

    finally:
        conn.close()


# ==========================================
# จำนวน Stock ทั้งหมด
# ==========================================

def get_stock_count():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT IFNULL(SUM(quantity), 0) AS total FROM stock"
            )

            row = cursor.fetchone()

        return int(row.get("total", 0)) if row else 0

    finally:
        conn.close()


# ==========================================
# จำนวนสินค้าใกล้หมด
# ==========================================

def get_low_stock_count():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) AS total FROM stock WHERE quantity <= 3"
            )

            row = cursor.fetchone()

        return int(row.get("total", 0)) if row else 0

    finally:
        conn.close()


# ==========================================
# รายการสินค้าใกล้หมด
# ==========================================

def get_low_stock_items():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    category,
                    size,
                    quantity
                FROM stock
                WHERE quantity <= 3
                ORDER BY quantity ASC
            """)

            rows = cursor.fetchall()

        return [
            (
                r["category"],
                r["size"],
                r["quantity"]
            )
            for r in rows
        ]

    finally:
        conn.close()


# ==========================================
# สินค้าขายดีที่สุด
# ==========================================

def get_top_product():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    CONCAT(category, ' ', size) AS item_name
                FROM sales
                GROUP BY category, size
                ORDER BY COUNT(*) DESC
                LIMIT 1
            """)

            row = cursor.fetchone()

        return (
            row["item_name"]
            if row and row.get("item_name")
            else "-"
        )

    finally:
        conn.close()


# ==========================================
# Top 5 Sales
# ==========================================

def get_top_sales():

    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            cursor.execute("""
                SELECT
                    category,
                    size,
                    COUNT(*) AS total_count
                FROM sales
                GROUP BY category, size
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """)

            rows = cursor.fetchall()

        return [
            (
                r["category"],
                r["size"],
                r["total_count"]
            )
            for r in rows
        ]

    finally:
        conn.close()