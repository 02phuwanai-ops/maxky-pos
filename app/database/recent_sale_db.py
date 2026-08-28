from datetime import datetime

from app.database.db import get_db_connection


def get_recent_sales(
    station_name: str = "จุดขายที่ 1",
    event_name: str = None
):
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:

            query = """
                SELECT
                    created_at,
                    category,
                    size,
                    price,
                    event_name,
                    payment_method,
                    station_name
                FROM sales
                WHERE station_name = %s
                  AND is_closed = 0
            """

            params = [station_name]

            # กรองตามชื่องานเฉพาะเมื่อมีการเลือกชื่องาน
            if event_name:
                query += " AND event_name = %s"
                params.append(event_name)

            query += """
                ORDER BY id DESC
                LIMIT 10
            """

            cursor.execute(
                query,
                tuple(params)
            )

            rows = cursor.fetchall()

    except Exception as e:
        print(f"Database Error in get_recent_sales: {e}")
        return []

    finally:
        conn.close()


    # ==========================================
    # แปลงข้อมูลสำหรับส่งกลับ API
    # ==========================================

    data = []

    for row in rows:

        created_at = row.get("created_at")
        category = row.get("category")
        size = row.get("size")

        price = (
            float(row.get("price", 0))
            if row.get("price") is not None
            else 0.0
        )

        row_event = row.get("event_name") or ""
        payment_method = (
            row.get("payment_method")
            or "เงินสด"
        )

        row_station = (
            row.get("station_name")
            or "จุดขายที่ 1"
        )


        # ==========================================
        # จัดรูปแบบวันที่
        # ==========================================

        display_time = "-"

        if isinstance(created_at, datetime):

            display_time = created_at.strftime(
                "%d/%m/%Y %H:%M"
            )

        elif created_at:

            try:

                created_str = str(created_at)

                date_part, time_part = (
                    created_str.split(" ")
                )

                year, month, day = (
                    date_part.split("-")
                )

                hour, minute = (
                    time_part.split(":")[:2]
                )

                display_time = (
                    f"{day}/{month}/{year} "
                    f"{hour}:{minute}"
                )

            except Exception:

                display_time = str(created_at)


        data.append({

            "datetime": display_time,

            "category": category,

            "size": size,

            "price": price,

            "event_name": row_event,

            "payment_method": payment_method,

            "station_name": row_station

        })


    return data