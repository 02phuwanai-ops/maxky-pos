import sqlite3
from datetime import datetime


DB_NAME = "data/maxky_pos.db"


# ==========================================
# รายงานวันนี้
# สามารถเลือกตามชื่องานได้
# ==========================================

def get_today_report(event_name=""):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    event_name = (event_name or "").strip()


    # ==========================================
    # เงื่อนไขชื่องาน
    # ==========================================

    if event_name:

        event_condition = """
            AND TRIM(event_name) = TRIM(?)
        """

    else:

        event_condition = ""


    # ==========================================
    # จำนวนขาย
    # ==========================================

    if event_name:

        cursor.execute(
            f"""
            SELECT COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            {event_condition}
            """,
            (
                today + "%",
                event_name
            )
        )

    else:

        cursor.execute(
            f"""
            SELECT COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            {event_condition}
            """,
            (
                today + "%",
            )
        )


    qty = cursor.fetchone()[0]


    # ==========================================
    # เงิน
    # ==========================================

    if event_name:

        cursor.execute(
            f"""
            SELECT

                SUM(price),

                SUM(cost),

                SUM(profit)

            FROM sales

            WHERE created_at LIKE ?

            {event_condition}
            """,
            (
                today + "%",
                event_name
            )
        )

    else:

        cursor.execute(
            f"""
            SELECT

                SUM(price),

                SUM(cost),

                SUM(profit)

            FROM sales

            WHERE created_at LIKE ?

            {event_condition}
            """,
            (
                today + "%",
            )
        )


    money = cursor.fetchone()


    sales = money[0] or 0

    cost = money[1] or 0

    profit = money[2] or 0


    # ==========================================
    # รายละเอียดสินค้า
    # ==========================================

    if event_name:

        cursor.execute(
            f"""
            SELECT

                category,

                size,

                COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            {event_condition}

            GROUP BY
                category,
                size

            ORDER BY
                category,
                size
            """,
            (
                today + "%",
                event_name
            )
        )

    else:

        cursor.execute(
            f"""
            SELECT

                category,

                size,

                COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            {event_condition}

            GROUP BY
                category,
                size

            ORDER BY
                category,
                size
            """,
            (
                today + "%",
            )
        )


    products = cursor.fetchall()


    conn.close()


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
