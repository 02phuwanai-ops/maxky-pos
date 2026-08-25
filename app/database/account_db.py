import sqlite3
from datetime import datetime, timezone, timedelta

# 🇹🇭 กำหนด Timezone ประเทศไทย (UTC+7)
tz_thai = timezone(timedelta(hours=7))

ACCOUNT_DB = "data/account.db"

def init_account_db():
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT DEFAULT 'ทั่วไป',
            scope TEXT DEFAULT 'personal',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_cleared INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(title: str, trans_type: str, amount: float, category: str, scope: str = "personal"):
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    
    # 👈 สร้างเวลาไทยปัจจุบันแบบชัดเจน (ส่งไปแทนที่ CURRENT_TIMESTAMP ของ SQLite)
    now_thai = datetime.now(tz_thai).strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
        INSERT INTO transactions (title, type, amount, category, scope, created_at, is_cleared)
        VALUES (?, ?, ?, ?, ?, ?, 0)
    """, (title, trans_type, amount, category, scope, now_thai))
    conn.commit()
    conn.close()

def delete_transaction(trans_id: int):
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM transactions WHERE id = ?", (trans_id,))
    conn.commit()
    conn.close()

def update_transaction(trans_id: int, title: str, trans_type: str, amount: float, category: str, scope: str = "personal"):
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE transactions 
        SET title = ?, type = ?, amount = ?, category = ?, scope = ?
        WHERE id = ?
    """, (title, trans_type, amount, category, scope, trans_id))
    conn.commit()
    conn.close()

def get_account_summary(selected_scope: str = "all", start_date: str = None, end_date: str = None):
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    
    # 1. เงื่อนไข Scope หลัก
    if selected_scope == "work":
        where_clause = " WHERE scope = 'work' AND (is_cleared IS NULL OR is_cleared = 0)"
    elif selected_scope == "personal":
        where_clause = " WHERE scope = 'personal'"
    else:
        where_clause = " WHERE (is_cleared IS NULL OR is_cleared = 0)"

    # 2. เพิ่มเงื่อนไขการกรองวันที่ (ถ้ามีการส่งมา)
    if start_date:
        where_clause += f" AND DATE(created_at) >= '{start_date}'"
    if end_date:
        where_clause += f" AND DATE(created_at) <= '{end_date}'"

    # 1. รายรับรวม
    cursor.execute(f"SELECT IFNULL(SUM(amount), 0) FROM transactions{where_clause} AND type = 'income'")
    income = cursor.fetchone()[0]
    
    # 2. รายจ่ายรวม
    cursor.execute(f"SELECT IFNULL(SUM(amount), 0) FROM transactions{where_clause} AND type = 'expense'")
    expense = cursor.fetchone()[0]
    
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
        "chart_data": [r[1] for r in cat_rows],
        "selected_scope": selected_scope
    }

def get_work_income_summary():
    """ดึงยอดกล่องสีเขียวรอบปัจจุบัน (ข้ามรายการที่เป็นบรรทัดสรุปจบงาน)"""
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT IFNULL(SUM(amount), 0) 
        FROM transactions 
        WHERE type = 'income' 
          AND scope = 'work' 
          AND (is_cleared IS NULL OR is_cleared = 0)
          AND title NOT LIKE 'สรุปยอดจบงาน%'
    """)
    total_work_income = cursor.fetchone()[0]
    conn.close()
    return total_work_income

def clear_work_income():
    """เคลียร์ยอดรอบปัจจุบัน"""
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    
    # 1. คำนวณยอดขายย่อยปัจจุบัน (ไม่รวมบรรทัดสรุปเก่า)
    cursor.execute("""
        SELECT IFNULL(SUM(amount), 0) 
        FROM transactions 
        WHERE type = 'income' 
          AND scope = 'work' 
          AND (is_cleared IS NULL OR is_cleared = 0)
          AND title NOT LIKE 'สรุปยอดจบงาน%'
    """)
    total_income = cursor.fetchone()[0]
    
    if total_income > 0:
        # 2. มาร์กรายการย่อยเดิมว่าเคลียร์แล้ว
        cursor.execute("""
            UPDATE transactions 
            SET is_cleared = 1 
            WHERE type = 'income' 
              AND scope = 'work' 
              AND (is_cleared IS NULL OR is_cleared = 0)
              AND title NOT LIKE 'สรุปยอดจบงาน%'
        """)
        
        # 3. บันทึกบรรทัดสรุปจบงาน (ใส่เวลาไทย)
        now_thai = datetime.now(tz_thai).strftime("%Y-%m-%d %H:%M:%S")
        summary_title = f"สรุปยอดจบงาน / เคลียร์ยอดรายรับ (รวม ฿{total_income:,.2f})"
        cursor.execute("""
            INSERT INTO transactions (title, type, amount, category, scope, created_at, is_cleared)
            VALUES (?, 'income', ?, 'ขายสินค้า', 'work', ?, 0)
        """, (summary_title, total_income, now_thai))
        
        conn.commit()
    
    conn.close()