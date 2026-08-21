from fastapi import APIRouter, Request, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import List, Optional

from app.database.product_db import get_products, get_product_price
from app.database.stock_db import get_sizes_by_product, reduce_stock, increase_stock, get_stock
from app.database.recent_sale_db import get_recent_sales
from app.database.sales_db import (
    add_sale,
    get_last_sale,
    delete_sale,
    get_shift_sales_summary,
    close_current_shift
)

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

# Helper คำนวณยอดสรุปแบบปลอดภัย
def _get_safe_summary(station_name: str, event_name: str = ""):
    try:
        res = get_shift_sales_summary(station_name, event_name)
    except TypeError:
        try:
            res = get_shift_sales_summary(station_name)
        except Exception:
            res = None

    if isinstance(res, dict):
        return {
            "total_items": res.get("total_items") or res.get("count") or 0,
            "total_revenue": res.get("total_revenue") or res.get("revenue") or 0,
            "cash": res.get("cash") or 0,
            "transfer": res.get("transfer") or 0,
            "half": res.get("half") or 0
        }
    return {"total_items": 0, "total_revenue": 0, "cash": 0, "transfer": 0, "half": 0}

# =====================================
# HTML Page Endpoint: /sale
# =====================================

@router.get("/sale", response_class=HTMLResponse)
def sale_page(request: Request):
    products = []
    for product in get_products():
        product_id, category = product[0], product[1]
        sizes = get_sizes_by_product(category)
        if not sizes:
            continue
        default_price = 0
        price_info = get_product_price(category, sizes[0])
        if price_info:
            _, default_price = price_info

        products.append({
            "id": product_id,
            "name": category,
            "sizes": sizes,
            "price": default_price
        })

    priority = {"เสื้อยืด": 1, "เสื้อกีฬา": 2, "เสื้อฟอก": 3}
    products.sort(key=lambda p: priority.get(p["name"], 99))

    recent_sales = get_recent_sales(station_name="จุดขายที่ 1")

    return templates.TemplateResponse(
        request=request,
        name="sale.html",
        context={
            "request": request,
            "products": products,
            "recent_sales": recent_sales
        }
    )

# =====================================
# API Endpoints
# =====================================

@router.post("/api/sell")
def api_sell(data: SellRequest):
    if not data.cart:
        return {"success": False, "message": "❌ ไม่มีรายการสินค้าในตะกร้า"}

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
            if not reduce_stock(category, size):
                for p in processed_items:
                    increase_stock(p["category"], p["size"])
                    delete_sale(p["sale_id"])
                return {"success": False, "message": f"❌ {category} {size} สต๊อกไม่พอ"}

            product = get_product_price(category, size)
            if not product:
                increase_stock(category, size)
                for p in processed_items:
                    increase_stock(p["category"], p["size"])
                    delete_sale(p["sale_id"])
                return {"success": False, "message": f"❌ ไม่พบข้อมูลราคาของ {category} {size}"}

            cost, price = product
            final_price = max(0.0, price - discount_per_item)

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
                return {"success": False, "message": "❌ ไม่สามารถบันทึกรายการขายได้"}

            processed_items.append({"sale_id": sale_id, "category": category, "size": size})
            success_sales.append({"sale_id": sale_id, "category": category, "size": size, "stock": get_stock(category, size)})

    summary = _get_safe_summary(station_name, event_name)
    return {
        "success": True,
        "message": "✅ ขายสำเร็จ",
        "sales": success_sales,
        "count": summary["total_items"],
        "revenue": summary["total_revenue"]
    }

@router.get("/api/recent-sales")
def recent_sales(
    station_name: Optional[str] = Query(None),
    station: Optional[str] = Query(None),
    event_name: Optional[str] = Query(None)
):
    selected_station = station_name or station or "จุดขายที่ 1"
    selected_event = event_name or ""
    
    try:
        sales_data = get_recent_sales(selected_station, selected_event)
    except TypeError:
        sales_data = get_recent_sales(selected_station)

    summary = _get_safe_summary(selected_station, selected_event)

    return {
        "success": True,
        "sales": sales_data,
        "count": summary["total_items"],
        "total_count": summary["total_items"],
        "revenue": summary["total_revenue"]
    }

@router.post("/api/undo-sale")
def undo_sale(data: Optional[ShiftRequest] = None):
    station_name = data.station_name if data and data.station_name else "จุดขายที่ 1"
    event_name = data.event_name if data and data.event_name else ""
    
    try:
        last = get_last_sale(station_name)
    except TypeError:
        last = get_last_sale()

    if not last:
        summary = _get_safe_summary(station_name, event_name)
        return {
            "success": False,
            "message": "❌ ไม่มีรายการขายให้ยกเลิก",
            "count": summary["total_items"],
            "revenue": summary["total_revenue"]
        }

    sale_id, category, size = last[0], last[1], last[2]

    if not increase_stock(category, size):
        return {"success": False, "message": f"❌ ไม่สามารถคืน Stock {category} {size} ได้"}

    if not delete_sale(sale_id):
        reduce_stock(category, size)
        return {"success": False, "message": "❌ ไม่สามารถลบรายการขายได้"}

    new_summary = _get_safe_summary(station_name, event_name)

    return {
        "success": True,
        "message": f"↩ ยกเลิก {category} {size} แล้ว",
        "sale_id": sale_id,
        "category": category,
        "size": size,
        "stock": get_stock(category, size),
        "count": new_summary["total_items"],
        "revenue": new_summary["total_revenue"]
    }

@router.get("/api/close-shift-summary")
@router.get("/api/shift-summary")
def api_shift_summary(
    station_name: Optional[str] = Query("จุดขายที่ 1"),
    event_name: Optional[str] = Query("")
):
    summary = _get_safe_summary(station_name, event_name)
    return {
        "success": True,
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
    
    # 🔍 พิมพ์ดูค่าที่ส่งมาจากหน้าเว็บ
    print(f"\n================ [DEBUG FRONTEND REQUEST] ================")
    print(f"📌 STATION RECEIVE : '{station_name}'")
    print(f"📌 EVENT RECEIVE   : '{event_name}'")
    print(f"======================================================\n")

    summary = close_current_shift(station_name, event_name)

    return {
        "success": True,
        "message": f"✅ ปิดยอดประจำวันเรียบร้อยแล้ว ({station_name})",
        "summary": summary
    }