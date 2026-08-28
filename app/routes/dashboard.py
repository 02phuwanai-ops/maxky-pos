import pymysql
from fastapi import APIRouter, Request
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
def dashboard(request: Request):

    if request.cookies.get("owner") != "yes":
        return RedirectResponse("/owner-login")

    # เรียก get_dashboard โดยไม่ล็อก station เพื่อดึงรายการขายล่าสุดในกะปัจจุบันทั้งหมด
    count, revenue, profit = get_dashboard()
    stock = get_stock_count()
    low_stock = get_low_stock_count()
    low_stock_items = get_low_stock_items()
    top_product = get_top_product()
    top_sales = get_top_sales()

    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "request": request,
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
# ROUTE ล้างข้อมูลยอดขาย (ใช้ MySQL อัปเดตผ่าน Database กลาง)
# ==========================================
@router.get("/api/clear-all-data")
@router.post("/api/clear-all-data")
def clear_all_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. ลบเฉพาะตารางประวัติการขายเท่านั้น
        cursor.execute("DELETE FROM sales;")
        
        # 2. ลบประวัติกะการขาย
        try:
            cursor.execute("DELETE FROM shifts;")
        except Exception:
            pass

        conn.commit()
        conn.close()

        return JSONResponse({
            "status": "success",
            "message": "รีเซ็ตยอดขายเรียบร้อยแล้ว (สต๊อกสินค้าคงเดิม 100%)"
        })
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "message": str(e)
        })