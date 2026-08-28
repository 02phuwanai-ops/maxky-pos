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

# ✨ 1. Import ฟังก์ชันจัดการบัญชีเข้ามาใช้งาน
from app.database.account_db import add_transaction

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
    event_name: Optional[str] = ""


# =====================================
# ขายสินค้า (ปรับแต่ง Response คืนค่าทนทานต่อ JS ทุกประเภท)
# =====================================

@router.post("/api/sell")
def api_sell(data: SellRequest):
    if not data.cart:
        return {
            "status": "error",
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
                    "status": "error",
                    "success": False,
                    "message": f"❌ {category} {size} สต๊อกไม่พอ"
                }

            product = get_product_price(category, size)
            if not product:
                increase_stock(category, size)
                _rollback_sales(processed_items)
                return {
                    "status": "error",
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
                    "status": "error",
                    "success": False,
                    "message": "❌ ไม่สามารถบันทึกรายการขายได้"
                }

            # บันทึกรายรับลงบัญชีร้านค้า
            try:
                add_transaction(
                    title=f"ขาย {category} ({size}) - {payment_method}",
                    trans_type="income",
                    amount=float(final_price),
                    category="ขายสินค้า",
                    scope="work"
                )
            except Exception as e:
                print(f"Error sync POS to Account DB: {e}")

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

    # ดึงยอดสรุปตาม Shift ( fallback ไปดึงยอดวันนี้ถ้า shift เป็น 0)
    try:
        shift_summary = get_shift_sales_summary(station_name, event_name)
    except Exception:
        shift_summary = {}

    cnt = shift_summary.get("total_items") if isinstance(shift_summary, dict) and shift_summary.get("total_items") else today_sales_count()
    rev = shift_summary.get("total_revenue") if isinstance(shift_summary, dict) and shift_summary.get("total_revenue") else today_sales_revenue()

    return {
        "status": "success",
        "success": True,
        "message": "✅ บันทึกการขายสำเร็จ",
        "sales": success_sales,
        "count": cnt,
        "total_count": cnt,
        "revenue": rev,
        "total_revenue": rev
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
    selected_station = station_name or station or "จุดขายที่ 1"
    
    try:
        sales_data = get_recent_sales(selected_station, event_name)
    except TypeError:
        sales_data = get_recent_sales(selected_station)

    try:
        shift_summary = get_shift_sales_summary(selected_station, event_name)
    except TypeError:
        shift_summary = {}

    total_count = shift_summary.get("total_items") if isinstance(shift_summary, dict) and shift_summary.get("total_items") else today_sales_count()
    total_rev = shift_summary.get("total_revenue") if isinstance(shift_summary, dict) and shift_summary.get("total_revenue") else today_sales_revenue()

    return {
        "status": "success",
        "success": True,
        "sales": sales_data,
        "count": total_count,
        "total_count": total_count,
        "revenue": total_rev,
        "total_revenue": total_rev
    }

# =====================================
# API สรุปยอด Shift ปัจจุบัน
# =====================================

@router.get("/api/close-shift-summary")
@router.get("/api/shift-summary")
def api_shift_summary(
    station_name: Optional[str] = Query("จุดขายที่ 1"),
    event_name: Optional[str] = Query("")
):
    try:
        summary = get_shift_sales_summary(station_name, event_name)
    except Exception:
        summary = {}

    if isinstance(summary, dict):
        return {
            "status": "success",
            "success": True,
            "total_items": summary.get("total_items", 0),
            "cash": summary.get("cash", 0),
            "transfer": summary.get("transfer", 0),
            "half": summary.get("half", 0),
            "total_revenue": summary.get("total_revenue", 0),
            "summary": summary
        }
    
    return {"status": "success", "success": True, "summary": summary}


# =====================================
# API กดปิดยอดประจำวัน
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
        "status": "success",
        "success": True,
        "message": f"✅ ปิดยอดประจำวันเรียบร้อยแล้ว ({station_name})",
        "summary": summary
    }