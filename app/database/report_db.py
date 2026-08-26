import pymysql
from datetime import datetime
from app.database.db import get_db_connection


# ==========================================
# รายงานวันนี้
# สามารถเลือกตามชื่องานได้
# ==========================================

def get_today_report(event_name=""):
    conn = get_db_connection()
    cursor = conn.cursor()

    today = datetime.now().strftime("%Y-%m-%d")
    event_name = (event_name or "").strip()

    # ==========================================
    # เงื่อนไขชื่องาน
    # ==========================================
    if event_name:
        event_condition = "AND TRIM(event_name) = TRIM(%s)"
        params_base = (today, event_name)
    else:
        event_condition = ""
        params_base = (today,)

    # ==========================================
    # 1. จำนวนขาย (QTY)
    # ==========================================
    query_qty = f"""
        SELECT COUNT(*) AS total_qty
        FROM sales
        WHERE DATE(created_at) = %s
        {event_condition}
    """
    cursor.execute(query_qty, params_base)
    row_qty = cursor.fetchone()
    
    if isinstance(row_qty, dict):
        qty = row_qty.get("total_qty") or 0
    elif row_qty:
        qty = row_qty[0] or 0
    else:
        qty = 0

    # ==========================================
    # 2. ยอดเงิน (Sales, Cost, Profit)
    # ==========================================
    query_money = f"""
        SELECT
            SUM(price) AS total_sales,
            SUM(cost) AS total_cost,
            SUM(profit) AS total_profit
        FROM sales
        WHERE DATE(created_at) = %s
        {event_condition}
    """
    cursor.execute(query_money, params_base)
    row_money = cursor.fetchone()

    if isinstance(row_money, dict):
        sales = float(row_money.get("total_sales") or 0)
        cost = float(row_money.get("total_cost") or 0)
        profit = float(row_money.get("total_profit") or 0)
    elif row_money:
        sales = float(row_money[0] or 0)
        cost = float(row_money[1] or 0)
        profit = float(row_money[2] or 0)
    else:
        sales, cost, profit = 0.0, 0.0, 0.0

    # ==========================================
    # 3. รายละเอียดสินค้า (Products Grouped)
    # ==========================================
    query_products = f"""
        SELECT
            category,
            size,
            COUNT(*) AS qty
        FROM sales
        WHERE DATE(created_at) = %s
        {event_condition}
        GROUP BY category, size
        ORDER BY category, size
    """
    cursor.execute(query_products, params_base)
    raw_products = cursor.fetchall()

    conn.close()

    # แปลงรูปแบบคืนค่าให้เป็น Tuple (category, size, count) เหมือนเดิม
    products = []
    for p in raw_products:
        if isinstance(p, dict):
            products.append((p.get("category"), p.get("size"), p.get("qty", 0)))
        else:
            products.append(p)

    # ==========================================
    # ส่งข้อมูลกลับ
    # ==========================================
    return {
        "qty": qty,
        "sales": sales,
        "cost": cost,
        "profit": profit,
        "products": products,
        "event_name": event_name
    }