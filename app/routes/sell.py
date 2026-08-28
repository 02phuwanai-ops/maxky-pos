from fastapi import APIRouter, BackgroundTasks  # 🎯 Import BackgroundTasks เพิ่ม
from pydantic import BaseModel, Field
from typing import List, Optional

from app.database.product_db import get_product_price
from app.database.stock_db import reduce_stock, increase_stock, get_stock
from app.database.sales_db import (
    add_sale, 
    today_sales_count, 
    today_sales_revenue
)

# Import account_db แบบปลอดภัย
try:
    from app.database.account_db import add_transaction
except ImportError:
    add_transaction = None

router = APIRouter()

# =====================================
# Pydantic Schemas
# =====================================

class CartItem(BaseModel):
    category: Optional[str] = Field(None, alias="category")
    name: Optional[str] = Field(None, alias="name")
    product_name: Optional[str] = Field(None, alias="product_name")
    
    size: str
    qty: Optional[int] = 1
    price: Optional[float] = 0.0

    class Config:
        populate_by_name = True

    @property
    def item_category(self) -> str:
        return self.category or self.name or self.product_name or ""

class BatchSellRequest(BaseModel):
    items: Optional[List[CartItem]] = None
    cart: Optional[List[CartItem]] = None
    discount: Optional[float] = 0.0
    payment_method: Optional[str] = "เงินสด"
    event_name: Optional[str] = ""
    station_name: Optional[str] = "จุดขายที่ 1"


# =====================================
# API Endpoints (Ultra-Fast Version)
# =====================================

@router.post("/api/sell-batch")
@router.post("/sell-batch")
def api_sell_batch(data: BatchSellRequest, background_tasks: BackgroundTasks):
    try:
        raw_items = data.items or data.cart or []
        if not raw_items:
            return {
                "status": "error",
                "success": False,
                "ok": False,
                "message": "❌ ไม่มีสินค้าในรายการ"
            }

        event_name = data.event_name.strip() if data.event_name else ""
        discount = data.discount if data.discount else 0.0
        payment_method = data.payment_method if data.payment_method else "เงินสด"
        station_name = data.station_name if data.station_name else "จุดขายที่ 1"

        expanded_items = []
        for item in raw_items:
            qty = item.qty if (item.qty and item.qty > 0) else 1
            for _ in range(qty):
                expanded_items.append(item)

        total_items = len(expanded_items)
        discount_per_item = discount / total_items if total_items > 0 else 0.0
        sold_count = 0
        success_sales = []

        for item in expanded_items:
            cat = item.item_category
            sz = item.size

            if not cat or not sz:
                continue

            # 1. ตัดสต็อก
            try:
                stock_ok = reduce_stock(cat, sz)
            except Exception as e:
                print(f"[ERROR reduce_stock]: {e}")
                stock_ok = False

            if not stock_ok:
                print(f"[SELL WARN] ตัดสต็อกไม่สำเร็จ: {cat} {sz}")
                continue

            # 2. ดึงราคา
            product = None
            try:
                product = get_product_price(cat, sz)
            except Exception as e:
                print(f"[ERROR get_product_price]: {e}")

            if not product:
                try:
                    increase_stock(cat, sz)
                except Exception:
                    pass
                print(f"[SELL WARN] ไม่พบราคา: {cat} {sz}")
                continue

            cost, price = product
            if price <= 0 and item.price and item.price > 0:
                price = item.price

            final_price = max(0.0, float(price) - discount_per_item)

            # 3. บันทึกลง DB การขาย (ยิงโดยตรง ไม่ทำ try-except ซ้ำซ้อน)
            sale_id = None
            try:
                sale_id = add_sale(cat, sz, cost, final_price, event_name, payment_method, station_name)
            except Exception as e:
                print(f"[ERROR add_sale]: {e}")

            if sale_id:
                sold_count += 1
                
                success_sales.append({
                    "sale_id": sale_id,
                    "category": cat,
                    "size": sz,
                    "stock": 0  # ส่งค่า mock ชั่วคราวไปก่อน เพื่อไม่ต้องยิง DB ดึง stock ซ้ำ
                })

                # 🎯 4. บันทึกบัญชี (Account DB) โยนไปทำเบื้องหลัง ไม่ต้องรอ Cloud ตอบกลับ!
                if add_transaction:
                    background_tasks.add_task(
                        add_transaction,
                        title=f"ขาย POS: {cat} ({sz}) - {payment_method}",
                        trans_type="income",
                        amount=float(final_price),
                        category="ขายสินค้า",
                        scope="work"
                    )

        if sold_count == 0:
            return {
                "status": "error",
                "success": False,
                "ok": False,
                "message": "❌ บันทึกการขายไม่สำเร็จ (สต็อกไม่พอ หรือไม่พบราคา)"
            }

        # 🎯 ดึงสรุปยอดขายรวมวันนี้
        cnt = 0
        rev = 0.0
        try:
            cnt = today_sales_count()
            rev = today_sales_revenue()
        except Exception:
            pass

        return {
            "status": "success",
            "success": True,
            "ok": True,
            "message": f"✅ บันทึกสำเร็จ {sold_count} รายการ",
            "sales": success_sales,
            "count": cnt,
            "total_count": cnt,
            "revenue": rev,
            "total_revenue": rev
        }

    except Exception as outer_err:
        print(f"\n❌ [CRITICAL ERROR IN /api/sell]: {outer_err}\n")
        return {
            "status": "error",
            "success": False,
            "ok": False,
            "message": f"Server Error: {str(outer_err)}"
        }