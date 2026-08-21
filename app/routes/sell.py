from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import List, Optional

from app.database.product_db import get_product_price
from app.database.stock_db import reduce_stock, increase_stock, get_stock
from app.database.sales_db import add_sale, today_sales_count

router = APIRouter()

class CartItem(BaseModel):
    category: str
    size: str
    qty: Optional[int] = 1
    price: Optional[float] = 0.0

class BatchSellRequest(BaseModel):
    items: Optional[List[CartItem]] = None
    cart: Optional[List[CartItem]] = None  # รองรับ key "cart" จาก JavaScript หน้าบ้าน
    discount: Optional[float] = 0.0
    payment_method: Optional[str] = "เงินสด"
    event_name: Optional[str] = ""
    station_name: Optional[str] = "จุดขายที่ 1"  # เพิ่มรองรับจุดขายที่ 1, 2, 3

@router.post("/api/sell")
@router.post("/sell")
@router.post("/api/sell-batch")
@router.post("/sell-batch")
async def api_sell_batch(data: BatchSellRequest):
    # รองรับทั้งแบบส่ง key "items" หรือ "cart"
    raw_items = data.items or data.cart or []
    if not raw_items:
        return {"success": False, "message": "ไม่มีสินค้าในรายการ"}

    # กระจายรายการตามจำนวน qty ที่ส่งมาจากหน้าบ้าน
    expanded_items = []
    for item in raw_items:
        qty = item.qty if item.qty and item.qty > 0 else 1
        for _ in range(qty):
            expanded_items.append(item)

    total_items = len(expanded_items)
    discount_per_item = data.discount / total_items if total_items > 0 else 0
    sold_count = 0

    for item in expanded_items:
        # ตัดสต็อก
        if not reduce_stock(item.category, item.size):
            continue

        # ดึงราคาทุนและราคาขาย
        product = get_product_price(item.category, item.size)
        if not product:
            increase_stock(item.category, item.size)
            continue

        cost, price = product
        final_price = max(0, price - discount_per_item)

        # บันทึกลงฐานข้อมูลแบบ fallback รองรับฟังก์ชั่น add_sale ทุกเวอร์ชัน
        try:
            add_sale(item.category, item.size, cost, final_price, data.event_name, data.payment_method, data.station_name)
        except TypeError:
            try:
                add_sale(item.category, item.size, cost, final_price, data.event_name, data.payment_method)
            except TypeError:
                try:
                    add_sale(item.category, item.size, cost, final_price, data.event_name)
                except TypeError:
                    add_sale(item.category, item.size, cost, final_price)

        sold_count += 1

    return {
        "success": True,
        "message": f"บันทึกสำเร็จ {sold_count} ตัว",
        "count": today_sales_count()
    }