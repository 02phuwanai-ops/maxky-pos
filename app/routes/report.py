from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

import sqlite3
from datetime import datetime

from app.database.sales_db import get_event_names


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)


DB_NAME = "data/maxky_pos.db"


@router.get(
    "/report",
    response_class=HTMLResponse
)
async def report(
    request: Request,
    event_name: str = ""
):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    today = datetime.now().strftime(
        "%Y-%m-%d"
    )


    # ==========================================
    # ชื่องานที่เลือก
    # ==========================================

    event_name = event_name.strip()


    # ==========================================
    # จำนวนขาย
    # ==========================================

    if event_name:

        cursor.execute(
            """
            SELECT COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            AND TRIM(event_name) = TRIM(?)
            """,

            (
                today + "%",
                event_name
            )
        )

    else:

        cursor.execute(
            """
            SELECT COUNT(*)

            FROM sales

            WHERE created_at LIKE ?
            """,

            (
                today + "%",
            )
        )


    total = cursor.fetchone()[0]


    # ==========================================
    # รายได้
    # ==========================================

    if event_name:

        cursor.execute(
            """
            SELECT COALESCE(
                SUM(price),
                0
            )

            FROM sales

            WHERE created_at LIKE ?

            AND TRIM(event_name) = TRIM(?)
            """,

            (
                today + "%",
                event_name
            )
        )

    else:

        cursor.execute(
            """
            SELECT COALESCE(
                SUM(price),
                0
            )

            FROM sales

            WHERE created_at LIKE ?
            """,

            (
                today + "%",
            )
        )


    revenue = cursor.fetchone()[0]


    # ==========================================
    # แยกตามประเภทสินค้า
    # ==========================================

    if event_name:

        cursor.execute(
            """
            SELECT
                category,
                COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            AND TRIM(event_name) = TRIM(?)

            GROUP BY category

            ORDER BY category
            """,

            (
                today + "%",
                event_name
            )
        )

    else:

        cursor.execute(
            """
            SELECT
                category,
                COUNT(*)

            FROM sales

            WHERE created_at LIKE ?

            GROUP BY category

            ORDER BY category
            """,

            (
                today + "%",
            )
        )


    rows = cursor.fetchall()


    conn.close()


    # ==========================================
    # รายชื่อชื่องานทั้งหมด
    # ==========================================

    event_names = get_event_names()


    # ==========================================
    # แสดง Report
    # ==========================================

    return templates.TemplateResponse(

        request=request,

        name="report.html",

        context={

            "total": total,

            "revenue": revenue,

            "items": rows,

            "event_names": event_names,

            "selected_event": event_name

        }

    )
