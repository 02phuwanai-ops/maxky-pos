import sqlite3

ACCOUNT_DB = "data/account.db"

def init_account_db():
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            type TEXT NOT NULL, -- 'income' (รายรับ) หรือ 'expense' (รายจ่าย)
            amount REAL NOT NULL,
            category TEXT DEFAULT 'ทั่วไป',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def add_transaction(title: str, trans_type: str, amount: float, category: str = "ทั่วไป"):
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (title, type, amount, category)
        VALUES (?, ?, ?, ?)
    """, (title, trans_type, amount, category))
    conn.commit()
    conn.close()

def get_transactions():
    init_account_db()
    conn = sqlite3.connect(ACCOUNT_DB)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, type, amount, category, created_at FROM transactions ORDER BY id DESC LIMIT 50")
    rows = cursor.fetchall()
    conn.close()
    return rows