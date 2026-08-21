from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.database.receive_db import (
    add_stock,
    get_recent_receive,
)

from app.database.product_db import get_products

from app.database.stock_db import (
    get_sizes,
    get_stock,
)


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)


# ==========================================
# หน้า Receive
# ==========================================

@router.get(
    "/receive",
    response_class=HTMLResponse
)
def receive_page(request: Request):

    product_buttons = ""

    for product in get_products():

        category = product[1]

        product_buttons += f"""
        <button
            type="button"
            class="product-btn"
            onclick="setProduct('{category}', this)"
        >
            {category}
        </button>
        """


    size_buttons = ""

    for size in get_sizes():

        size_buttons += f"""
        <button
            type="button"
            class="size-btn"
            onclick="setSize('{size}', this)"
        >
            {size}
        </button>
        """


    return templates.TemplateResponse(
        request=request,
        name="receive.html",
        context={
            "request": request,
            "title": "Receive",
            "product_buttons": product_buttons,
            "size_buttons": size_buttons,
        }
    )


# ==========================================
# รับสินค้าเข้าแบบ Form
# ==========================================

@router.post("/receive")
def receive_stock(
    category: str = Form(...),
    size: str = Form(...),
    quantity: int = Form(...)
):

    add_stock(
        category,
        size,
        quantity
    )

    return RedirectResponse(
        url="/receive",
        status_code=303
    )


# ==========================================
# API รับสินค้าเข้า
# ==========================================

@router.post("/api/receive")
def api_receive(
    category: str = Form(...),
    size: str = Form(...),
    quantity: int = Form(...)
):

    add_stock(
        category,
        size,
        quantity
    )

    remaining = get_stock(
        category,
        size
    )

    return JSONResponse({

        "success": True,

        "message": f"✅ รับ {category} {size} จำนวน {quantity} ตัว",

        "category": category,

        "size": size,

        "quantity": quantity,

        "stock": remaining

    })


# ==========================================
# API ดู Stock ของสินค้า + ไซส์
# ==========================================

@router.get("/api/receive-stock")
def receive_stock_info(
    category: str,
    size: str
):

    stock = get_stock(
        category,
        size
    )

    return {

        "success": True,

        "category": category,

        "size": size,

        "stock": stock

    }


# ==========================================
# API รับเข้าล่าสุด
# ==========================================

@router.get("/api/recent-receive")
def recent_receive():

    return {

        "items": get_recent_receive()

    }

