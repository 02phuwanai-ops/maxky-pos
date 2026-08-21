from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional

from app.database.recent_sale_db import get_recent_sales
from app.database.product_db import get_product_price

from app.database.stock_db import (
    reduce_stock,
    increase_stock,
    get_stock
)

from app.database.sales_db import (
    add_sale,
    today_sales_count,
    today_sales_revenue,
    get_last_sale,
    delete_sale,
    get_shift_sales_summary,
    close_current_shift
)

router = APIRouter()

# =====================================
# Pydantic Schemas
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
    event_name: Optional[str] = ""  # 🆕 เพิ่มให้รองรับชื่องาน


# =====================================
# ขายสินค้า
# =====================================

@router.post("/api/sell")
def api_sell(data: SellRequest):
    if not data.cart:
        return {
            "success": False,
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
        category = item.category
        size = item.size
        qty = item.qty

        for _ in range(qty):
            stock_ok = reduce_stock(category, size)
            if not stock_ok:
                _rollback_sales(processed_items)
                return {
                    "success": False,
                    "message": f"❌ {category} {size} สต๊อกไม่พอ"
                }

            product = get_product_price(category, size)
            if not product:
                increase_stock(category, size)
                _rollback_sales(processed_items)
                return {
                    "success": False,
                    "message": f"❌ ไม่พบข้อมูลราคาของ {category} {size}"
                }

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
                _rollback_sales(processed_items)
                return {
                    "success": False,
                    "message": "❌ ไม่สามารถบันทึกรายการขายได้"
                }

            processed_items.append({
                "sale_id": sale_id,
                "category": category,
                "size": size
            })

            success_sales.append({
                "sale_id": sale_id,
                "category": category,
                "size": size,
                "stock": get_stock(category, size)
            })

    # ดึงยอดสรุปตาม Shift
    try:
        shift_summary = get_shift_sales_summary(station_name, event_name)
    except TypeError:
        shift_summary = get_shift_sales_summary(station_name)

    return {
        "success": True,
        "message": "✅ ขายสำเร็จ",
        "sales": success_sales,
        "count": shift_summary.get("total_items", 0) if isinstance(shift_summary, dict) else 0,
        "revenue": shift_summary.get("total_revenue", 0) if isinstance(shift_summary, dict) else 0
    }


def _rollback_sales(processed_items: list):
    for item in processed_items:
        increase_stock(item["category"], item["size"])
        delete_sale(item["sale_id"])


# =====================================
# ขายล่าสุด
# =====================================

@router.get("/api/recent-sales")
def recent_sales(
    station_name: Optional[str] = Query(None),
    station: Optional[str] = Query(None),
    event_name: Optional[str] = Query(None)
):
    # บังคับคืนค่าเป็นรายการว่าง และยอดเป็น 0 ทั้งหมด
    return {
        "success": True,
        "sales": [],
        "count": 0,
        "total_count": 0,
        "revenue": 0
    }


# =====================================
# Undo Sale
# =====================================

@router.post("/api/undo-sale")
def undo_sale(data: Optional[ShiftRequest] = None):
    station_name = data.station_name if data and data.station_name else "จุดขายที่ 1"
    event_name = data.event_name if data and data.event_name else ""
    
    try:
        last = get_last_sale(station_name)
    except TypeError:
        last = get_last_sale()

    try:
        shift_summary = get_shift_sales_summary(station_name, event_name)
    except TypeError:
        shift_summary = get_shift_sales_summary(station_name)

    if not last:
        return {
            "success": False,
            "message": "❌ ไม่มีรายการขายให้ยกเลิก",
            "count": shift_summary.get("total_items", 0) if isinstance(shift_summary, dict) else 0,
            "revenue": shift_summary.get("total_revenue", 0) if isinstance(shift_summary, dict) else 0
        }

    sale_id, category, size = last[0], last[1], last[2]

    stock_ok = increase_stock(category, size)
    if not stock_ok:
        return {
            "success": False,
            "message": f"❌ ไม่สามารถคืน Stock {category} {size} ได้"
        }

    deleted = delete_sale(sale_id)
    if not deleted:
        reduce_stock(category, size)
        return {
            "success": False,
            "message": "❌ ไม่สามารถลบรายการขายได้"
        }

    try:
        shift_summary = get_shift_sales_summary(station_name, event_name)
    except TypeError:
        shift_summary = get_shift_sales_summary(station_name)

    return {
        "success": True,
        "message": f"↩ ยกเลิก {category} {size} แล้ว",
        "sale_id": sale_id,
        "category": category,
        "size": size,
        "stock": get_stock(category, size),
        "count": shift_summary.get("total_items", 0) if isinstance(shift_summary, dict) else 0,
        "revenue": shift_summary.get("total_revenue", 0) if isinstance(shift_summary, dict) else 0
    }


# =====================================
# 🆕 API ดูสรุปยอด Shift ปัจจุบัน (รองรับทั้ง /api/close-shift-summary และ /api/shift-summary)
# =====================================

@router.get("/api/close-shift-summary")
@router.get("/api/shift-summary")
def api_shift_summary(
    station_name: Optional[str] = Query("จุดขายที่ 1"),
    event_name: Optional[str] = Query("")
):
    try:
        summary = get_shift_sales_summary(station_name, event_name)
    except TypeError:
        summary = get_shift_sales_summary(station_name)

    if isinstance(summary, dict):
        return {
            "success": True,
            "total_items": summary.get("total_items", 0),
            "cash": summary.get("cash", 0),
            "transfer": summary.get("transfer", 0),
            "half": summary.get("half", 0),
            "total_revenue": summary.get("total_revenue", 0),
            "summary": summary
        }
    
    return {"success": True, "summary": summary}


# =====================================
# 🆕 API กดปิดยอดประจำวัน
# =====================================

@router.post("/api/close-shift")
def api_close_shift(data: ShiftRequest):
    station_name = data.station_name if data.station_name else "จุดขายที่ 1"
    event_name = data.event_name if data.event_name else ""
    
    try:
        summary = close_current_shift(station_name, event_name)
    except TypeError:
        summary = close_current_shift(station_name)

    return {
        "success": True,
        "message": f"✅ ปิดยอดประจำวันเรียบร้อยแล้ว ({station_name})",
        "summary": summary
    }