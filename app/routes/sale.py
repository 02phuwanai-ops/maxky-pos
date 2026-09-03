import io
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from app.database.account_db import add_transaction, delete_last_work_transaction
from app.database.product_db import get_product_price, get_sale_products
from app.database.recent_sale_db import get_recent_sales
from app.database.sales_db import (
    add_sale,
    close_current_shift,
    delete_sale,
    get_last_sale,
    get_shift_sales_summary,
    today_sales_count,
    today_sales_revenue,
)
from app.database.stock_db import get_stock, increase_stock, reduce_stock

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# =====================================
# Schemas
# =====================================

class CartItem(BaseModel):
    category: str
    size: str
    qty: int = 1

class SellRequest(BaseModel):
    cart: List[CartItem]
    event_name: Optional[str] = ""
    discount: Optional[float] = 0.0
    payment_method: Optional[str] = "เงินสด"
    station_name: Optional[str] = "จุดขายที่ 1"

class ShiftRequest(BaseModel):
    station_name: Optional[str] = "จุดขายที่ 1"
    event_name: Optional[str] = ""

# Helper บันทึกบัญชีเบื้องหลัง
def _async_add_transaction(title: str, trans_type: str, amount: float, category: str, scope: str = "work"):
    try:
        add_transaction(
            title=title,
            trans_type=trans_type,
            amount=amount,
            category=category,
            scope=scope
        )
    except Exception as e:
        print(f"Error syncing to Account DB: {e}")

# Helper ลบรายการบัญชีเบื้องหลัง (เมื่อยกเลิกการขาย)
def _async_delete_transaction(amount: float):
    try:
        delete_last_work_transaction(amount=amount)
    except Exception as e:
        print(f"Error deleting transaction from Account DB: {e}")

# Helper คำนวณยอดสรุปแบบปลอดภัย
def _get_safe_summary(station_name: str, event_name: str = ""):
    res = None
    try:
        res = get_shift_sales_summary(station_name, event_name)
    except TypeError:
        try:
            res = get_shift_sales_summary(station_name)
        except Exception:
            res = None
    except Exception:
        res = None

    cnt = 0
    rev = 0
    cash = 0
    transfer = 0
    half = 0

    if isinstance(res, dict):
        cnt = res.get("total_items") or res.get("count") or 0
        rev = res.get("total_revenue") or res.get("revenue") or 0
        cash = res.get("cash") or 0
        transfer = res.get("transfer") or 0
        half = res.get("half") or 0

    if cnt == 0:
        try:
            cnt = today_sales_count()
        except Exception:
            cnt = 0

    if rev == 0:
        try:
            rev = today_sales_revenue()
        except Exception:
            rev = 0.0

    return {
        "total_items": int(cnt),
        "total_revenue": float(rev),
        "cash": float(cash),
        "transfer": float(transfer),
        "half": float(half)
    }

# =====================================
# HTML Page Endpoint: /sale
# =====================================

@router.get("/sale", response_class=HTMLResponse)
def sale_page(request: Request):
    try:
        products = get_sale_products()
        priority = {
            "เสื้อยืด": 1,
            "เสื้อกีฬา": 2,
            "เสื้อฟอก": 3
        }
        products.sort(
            key=lambda p: priority.get(p["name"], 99)
        )
    except Exception as e:
        print(f"Error loading products for /sale: {e}")
        products = []

    return templates.TemplateResponse(
        request=request,
        name="sale.html",
        context={
            "request": request,
            "products": products,
            "recent_sales": []
        }
    )

# =====================================
# API Endpoints
# =====================================

@router.post("/api/sell")
def api_sell(data: SellRequest, background_tasks: BackgroundTasks):
    if not data.cart:
        return {
            "status": "error",
            "success": False,
            "ok": False,
            "message": "❌ ไม่มีรายการสินค้าในตะกร้า"
        }

    event_name = data.event_name.strip() if data.event_name else ""
    discount = data.discount if data.discount else 0.0
    payment_method = data.payment_method if data.payment_method else "เงินสด"
    station_name = data.station_name if data.station_name else "จุดขายที่ 1"
    
    total_qty = sum(item.qty for item in data.cart)
    discount_per_item = discount / total_qty if total_qty > 0 else 0.0

    success_sales = []
    processed_items = []

    for item in data.cart:
        category, size, qty = item.category, item.size, item.qty
        for _ in range(qty):
            # 1. ตรวจสอบและตัดสต็อก
            if not reduce_stock(category, size):
                for p in processed_items:
                    increase_stock(p["category"], p["size"])
                    delete_sale(p["sale_id"])
                return {
                    "status": "error",
                    "success": False,
                    "ok": False,
                    "message": f"❌ {category} {size} สต๊อกไม่พอ"
                }

            # 2. ดึงราคา
            product = get_product_price(category, size)
            if not product:
                increase_stock(category, size)
                for p in processed_items:
                    increase_stock(p["category"], p["size"])
                    delete_sale(p["sale_id"])
                return {
                    "status": "error",
                    "success": False,
                    "ok": False,
                    "message": f"❌ ไม่พบข้อมูลราคาของ {category} {size}"
                }

            cost, price = product
            final_price = max(0.0, price - discount_per_item)

            # 3. บันทึกรายการขาย
            sale_id = add_sale(
                category=category,
                size=size,
                cost=cost,
                price=final_price,
                event_name=event_name,
                payment_method=payment_method,
                station_name=station_name
            )

            if not sale_id:
                increase_stock(category, size)
                for p in processed_items:
                    increase_stock(p["category"], p["size"])
                    delete_sale(p["sale_id"])
                return {
                    "status": "error",
                    "success": False,
                    "ok": False,
                    "message": "❌ ไม่สามารถบันทึกรายการขายได้"
                }

            processed_items.append({"sale_id": sale_id, "category": category, "size": size, "price": final_price})
            success_sales.append({"sale_id": sale_id, "category": category, "size": size})

            # บันทึกบัญชีรายรับเบื้องหลัง
            background_tasks.add_task(
                _async_add_transaction,
                title=f"ขาย POS: {category} ({size}) - {payment_method}",
                trans_type="income",
                amount=float(final_price),
                category="ขายสินค้า",
                scope="work"
            )

    return {
        "status": "success",
        "success": True,
        "ok": True,
        "message": "✅ ขายสำเร็จ",
        "sales": success_sales        
    }

@router.get("/get_recent_sales")
@router.get("/recent-sales")
@router.get("/api/recent-sales")
def recent_sales(
    station_name: Optional[str] = Query(None),
    station: Optional[str] = Query(None),
    event_name: Optional[str] = Query(None)
):
    selected_station = station_name or station or "จุดขายที่ 1"
    selected_event = event_name or ""
    
    sales_data = []
    try:
        try:
            sales_data = get_recent_sales(selected_station, selected_event)
        except TypeError:
            sales_data = get_recent_sales(selected_station)
    except Exception as e:
        print(f"Error fetching recent sales: {e}")

    summary = _get_safe_summary(selected_station, selected_event)

    return {
        "status": "success",
        "success": True,
        "ok": True,
        "sales": sales_data if isinstance(sales_data, list) else [],
        "count": summary["total_items"],
        "total_count": summary["total_items"],
        "revenue": summary["total_revenue"],
        "total_revenue": summary["total_revenue"]
    }

@router.post("/api/undo-sale")
def undo_sale(background_tasks: BackgroundTasks, data: Optional[ShiftRequest] = None):
    station_name = data.station_name if data and data.station_name else "จุดขายที่ 1"
    event_name = data.event_name if data and data.event_name else ""
    
    try:
        last = get_last_sale(station_name)
    except TypeError:
        last = get_last_sale()
    except Exception as e:
        print(f"Error getting last sale: {e}")
        last = None

    if not last:
        summary = _get_safe_summary(station_name, event_name)
        return {
            "status": "error",
            "success": False,
            "ok": False,
            "message": "❌ ไม่มีรายการขายให้ยกเลิก",
            "count": summary["total_items"],
            "revenue": summary["total_revenue"]
        }

    if isinstance(last, dict):
        sale_id = last.get("id")
        category = last.get("category")
        size = last.get("size")
        price = last.get("price", 0.0)
    elif isinstance(last, (list, tuple)):
        sale_id = last[0]
        category = last[1]
        size = last[2]
        price = last[3] if len(last) > 3 else 0.0
    else:
        sale_id = getattr(last, "id", None)
        category = getattr(last, "category", None)
        size = getattr(last, "size", None)
        price = getattr(last, "price", 0.0)

    if not category or not size:
        return {
            "status": "error",
            "success": False,
            "ok": False,
            "message": "❌ ข้อมูลรายการขายล่าสุดไม่ถูกต้อง"
        }

    # 1. คืนสต็อก
    if not increase_stock(category, size):
        return {
            "status": "error",
            "success": False,
            "ok": False,
            "message": f"❌ ไม่สามารถคืน Stock {category} {size} ได้"
        }

    # 2. ลบรายการขาย
    if not delete_sale(sale_id):
        reduce_stock(category, size)
        return {
            "status": "error",
            "success": False,
            "ok": False,
            "message": "❌ ไม่สามารถลบรายการขายได้"
        }

    # 3. ลบรายการรายรับออกจากหน้า งาน/ร้านค้า ทันที
    delete_last_work_transaction()

    return {
        "status": "success",
        "success": True,
        "ok": True,
        "message": f"↩ ยกเลิก {category} {size} เรียบร้อยแล้ว",
        "sale_id": sale_id,
        "category": category,
        "size": size        
    }

@router.get("/api/close-shift-summary")
@router.get("/api/shift-summary")
def api_shift_summary(
    station_name: Optional[str] = Query("จุดขายที่ 1"),
    event_name: Optional[str] = Query("")
):
    summary = _get_safe_summary(station_name, event_name)
    return {
        "status": "success",
        "success": True,
        "ok": True,
        "total_items": summary["total_items"],
        "cash": summary["cash"],
        "transfer": summary["transfer"],
        "half": summary["half"],
        "total_revenue": summary["total_revenue"],
        "summary": summary
    }

@router.post("/api/close-shift")
def api_close_shift(data: ShiftRequest):
    station_name = data.station_name if data.station_name else "จุดขายที่ 1"
    event_name = data.event_name if data.event_name else ""

    try:
        summary = close_current_shift(station_name, event_name)
    except Exception as e:
        print(f"Error closing shift: {e}")
        summary = {}

    return {
        "status": "success",
        "success": True,
        "ok": True,
        "message": f"✅ ปิดยอดประจำวันเรียบร้อยแล้ว ({station_name})",
        "summary": summary
    }