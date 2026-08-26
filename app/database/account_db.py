import os
import pymysql
from datetime import datetime, timezone, timedelta

# 🇹🇭 กำหนด Timezone ประเทศไทย (UTC+7)
tz_thai = timezone(timedelta(hours=7))

def get_db_connection():
    """สร้าง Connection เชื่อมต่อไปยัง MySQL (Aiven)"""
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "localhost"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", ""),
        database=os.getenv("MYSQL_DATABASE", "defaultdb"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        autocommit=True
    )

def init_account_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            category VARCHAR(100) DEFAULT 'ทั่วไป',
            scope VARCHAR(50) DEFAULT 'personal',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_cleared INT DEFAULT 0
        )
    """)
    conn.close()

def add_transaction(title: str, trans_type: str, amount: float, category: str, scope: str = "personal"):
    init_account_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    now_thai = datetime.now(tz_thai).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO transactions (title, type, amount, category, scope, created_at, is_cleared)
        VALUES (%s, %s, %s, %s, %s, %s, 0)
    """, (title, trans_type, amount, category, scope, now_thai))
    conn.close()

def delete_transaction(trans_id: int):
    init_account_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = %s", (trans_id,))
    conn.close()

def update_transaction(trans_id: int, title: str, trans_type: str, amount: float, category: str, scope: str = "personal"):
    init_account_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE transactions 
        SET title = %s, type = %s, amount = %s, category = %s, scope = %s
        WHERE id = %s
    """, (title, trans_type, amount, category, scope, trans_id))
    conn.close()

def get_account_summary(selected_scope: str = "all", start_date: str = None, end_date: str = None):
    init_account_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. เงื่อนไข Scope หลัก
    if selected_scope == "work":
        where_clause = " WHERE scope = 'work' AND (is_cleared IS NULL OR is_cleared = 0)"
    elif selected_scope == "personal":
        where_clause = " WHERE scope = 'personal'"
    else:
        where_clause = " WHERE (is_cleared IS NULL OR is_cleared = 0)"

    # 2. เพิ่มเงื่อนไขการกรองวันที่
    if start_date:
        where_clause += f" AND DATE(created_at) >= '{start_date}'"
    if end_date:
        where_clause += f" AND DATE(created_at) <= '{end_date}'"

    # 1. รายรับรวม
    cursor.execute(f"SELECT IFNULL(SUM(amount), 0) FROM transactions{where_clause} AND type = 'income'")
    income = float(cursor.fetchone()[0])
    
    # 2. รายจ่ายรวม
    cursor.execute(f"SELECT IFNULL(SUM(amount), 0) FROM transactions{where_clause} AND type = 'expense'")
    expense = float(cursor.fetchone()[0])
    
    # 3. ตารางประวัติรายการล่าสุด
    cursor.execute(f"SELECT id, title, type, amount, category, created_at, scope FROM transactions{where_clause} ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    
    # 4. กราฟสัดส่วนรายจ่าย
    cursor.execute(f"SELECT category, SUM(amount) FROM transactions{where_clause} AND type = 'expense' GROUP BY category")
    cat_rows = cursor.fetchall()
    
    conn.close()
    
    return {
        "income": income,
        "expense": expense,
        "balance": income - expense,
        "transactions": rows,
        "chart_labels": [r[0] for r in cat_rows],
        "chart_data": [float(r[1]) for r in cat_rows],
        "selected_scope": selected_scope
    }

def get_work_income_summary():
    """ดึงยอดกล่องสีเขียวรอบปัจจุบัน"""
    init_account_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT IFNULL(SUM(amount), 0) 
        FROM transactions 
        WHERE type = 'income' 
          AND scope = 'work' 
          AND (is_cleared IS NULL OR is_cleared = 0)
          AND title NOT LIKE 'สรุปยอดจบงาน%%'
    """)
    total_work_income = float(cursor.fetchone()[0])
    conn.close()
    return total_work_income

def clear_work_income():
    """เคลียร์ยอดรอบปัจจุบัน"""
    init_account_db()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. คำนวณยอดขายย่อยปัจจุบัน
    cursor.execute("""
        SELECT IFNULL(SUM(amount), 0) 
        FROM transactions 
        WHERE type = 'income' 
          AND scope = 'work' 
          AND (is_cleared IS NULL OR is_cleared = 0)
          AND title NOT LIKE 'สรุปยอดจบงาน%%'
    """)
    total_income = float(cursor.fetchone()[0])
    
    if total_income > 0:
        # 2. มาร์กรายการย่อยเดิมว่าเคลียร์แล้ว
        cursor.execute("""
            UPDATE transactions 
            SET is_cleared = 1 
            WHERE type = 'income' 
              AND scope = 'work' 
              AND (is_cleared IS NULL OR is_cleared = 0)
              AND title NOT LIKE 'สรุปยอดจบงาน%%'
        """)
        
        # 3. บันทึกบรรทัดสรุปจบงาน
        now_thai = datetime.now(tz_thai).strftime("%Y-%m-%d %H:%M:%S")
        summary_title = f"สรุปยอดจบงาน / เคลียร์ยอดรายรับ (รวม ฿{total_income:,.2f})"
        cursor.execute("""
            INSERT INTO transactions (title, type, amount, category, scope, created_at, is_cleared)
            VALUES (%s, 'income', %s, 'ขายสินค้า', 'work', %s, 0)
        """, (summary_title, total_income, now_thai))
        
    conn.close()