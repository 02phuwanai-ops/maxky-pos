import pymysql
from typing import Optional
from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.database.dashboard_db import (
    get_dashboard,
    get_stock_count,
    get_low_stock_count,
    get_low_stock_items,
    get_top_product,
    get_top_sales,
    get_db_connection
)

from app.database.stock_db import (
    get_stock_groups,
    get_total_stock
)

templates = Jinja2Templates(
    directory="app/templates"
)

router = APIRouter()


@router.get(
    "/dashboard",
    response_class=HTMLResponse
)
def dashboard(
    request: Request,
    event_name: Optional[str] = Query(None),
    date: Optional[str] = Query(None)
):

    if request.cookies.get("owner") != "yes":
        return RedirectResponse("/owner-login")

    # 1. ดึงรายชื่ออีเวนต์ทั้งหมดจากฐานข้อมูล (แก้ไขคำสั่ง SQL ให้ถูกต้องไม่ติด Error)
    event_names = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT event_name 
                FROM sales 
                WHERE event_name IS NOT NULL AND event_name != '' 
                GROUP BY event_name 
                ORDER BY MAX(created_at) DESC
            """)
            rows = cursor.fetchall()
            for row in rows:
                name = row["event_name"] if isinstance(row, dict) else row[0]
                if name:
                    event_names.append(name)
        conn.close()
    except Exception as e:
        print("Error loading events:", e) # ปริ้นท์ดูข้อผิดพลาดได้หากยังมีปัญหา

    # 2. ดึงยอดขายตามเงื่อนไข (ผ่านฟังก์ชันกลางที่ปรับปรุงแล้ว)
    count, revenue, profit = get_dashboard(event_name=event_name, date=date)

    # 3. ดึงรายการสินค้าขายดี (Top Sales) ตามเงื่อนไข
    top_sales = []
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql_top = """
                SELECT category, size, COUNT(*) as qty 
                FROM sales 
                WHERE 1=1
            """
            top_params = []
            
            # ถ้าไม่ได้เลือกงาน ให้ดูเฉพาะกะปัจจุบัน
            if not event_name and not date:
                sql_top += " AND is_closed = 0"

            if event_name:
                sql_top += " AND TRIM(event_name) = TRIM(%s)"
                top_params.append(event_name)
            if date:
                sql_top += " AND DATE(created_at) = %s"
                top_params.append(date)

            sql_top += " GROUP BY category, size ORDER BY qty DESC LIMIT 5"
            cursor.execute(sql_top, tuple(top_params))
            top_sales = cursor.fetchall()
        conn.close()
    except Exception:
        top_sales = []

    stock = get_stock_count()
    low_stock = get_low_stock_count()
    low_stock_items = get_low_stock_items()
    top_product = get_top_product()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
            "event_names": event_names,
            "selected_event": event_name or "",
            "selected_date": date or "",
            "count": count,
            "revenue": revenue,
            "profit": profit,
            "stock": stock,
            "low_stock": low_stock,
            "low_stock_items": low_stock_items,
            "top_product": top_product,
            "top_sales": top_sales
        }
    )


@router.get("/api/dashboard-stock")
def dashboard_stock():
    return JSONResponse({
        "total": get_total_stock(),
        "stock": get_stock_groups()
    })


@router.get("/api/stock-group")
def stock_group():
    groups = get_stock_groups()
    return JSONResponse({
        "groups": groups
    })


# ==========================================
# ROUTE จบงาน (เปลี่ยนสถานะเป็นปิดกะ แทนการลบข้อมูลทิ้ง)
# ==========================================
@router.get("/api/clear-all-data")
@router.post("/api/clear-all-data")
def clear_all_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # เปลี่ยนจาก DELETE เป็นการอัปเดต is_closed = 1 เพื่อเก็บประวัติและชื่องานไว้ดูย้อนหลัง
        cursor.execute("UPDATE sales SET is_closed = 1 WHERE is_closed = 0;")
        
        try:
            cursor.execute("DELETE FROM shifts;")
        except Exception:
            pass

        conn.commit()
        conn.close()

        return JSONResponse({
            "status": "success",
            "message": "จบงานเรียบร้อยแล้ว (ข้อมูลประวัติและชื่องานเก่าถูกบันทึกเก็บไว้ครบถ้วน)"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        })