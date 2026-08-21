from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.database.product_db import (
    get_products,
    get_product_sizes,
    add_product,
    add_product_price,
    update_product_price,
    delete_product_price,
    delete_product,
    update_product_name,
)

from app.database.stock_db import (
    create_product_stock,
    get_stock,
)

import sqlite3


DB_NAME = "data/maxky_pos.db"


router = APIRouter()


templates = Jinja2Templates(
    directory="app/templates"
)


# ==========================================
# Product Manager
# ==========================================

@router.get(
    "/products",
    response_class=HTMLResponse
)
def product_page(request: Request):

    rows = []

    for product in get_products():

        product_id = product[0]
        category = product[1]

        price_rows = get_product_sizes(product_id)

        sizes = []

        for item in price_rows:

            price_id = item[0]
            size = item[1]
            cost = item[2]
            price = item[3]

            stock = get_stock(
                category,
                size
            )

            sizes.append(
                (
                    price_id,
                    size,
                    cost,
                    price,
                    stock
                )
            )

        rows.append({

            "id": product_id,

            "category": category,

            "sizes": sizes

        })

    return templates.TemplateResponse(

        request=request,

        name="products.html",

        context={

            "request": request,

            "products": rows

        }

    )


# ==========================================
# Add Product
# ==========================================

@router.post("/products/add")
def add_new_product(

    category: str = Form(...),

    cost_s: float = Form(...),
    price_s: float = Form(...),
    stock_s: int = Form(0),

    cost_m: float = Form(...),
    price_m: float = Form(...),
    stock_m: int = Form(0),

    cost_l: float = Form(...),
    price_l: float = Form(...),
    stock_l: int = Form(0),

    cost_xl: float = Form(...),
    price_xl: float = Form(...),
    stock_xl: int = Form(0),

    cost_2xl: float = Form(...),
    price_2xl: float = Form(...),
    stock_2xl: int = Form(0),

    cost_3xl: float = Form(...),
    price_3xl: float = Form(...),
    stock_3xl: int = Form(0)

):

    category = category.strip()


    # ======================================
    # ตรวจสอบชื่อสินค้า
    # ======================================

    if not category:

        return HTMLResponse(
            """
            <script>

                alert("❌ กรุณากรอกชื่อสินค้า");

                window.location.href="/products";

            </script>
            """
        )


    # ======================================
    # ตรวจสอบ Stock
    # ======================================

    stocks = [

        stock_s,
        stock_m,
        stock_l,
        stock_xl,
        stock_2xl,
        stock_3xl

    ]

    if any(stock < 0 for stock in stocks):

        return HTMLResponse(
            """
            <script>

                alert("❌ Stock ต้องไม่ติดลบ");

                window.location.href="/products";

            </script>
            """
        )


    # ======================================
    # ตรวจสอบสินค้าซ้ำ
    # ======================================

    existing_products = get_products()

    for product in existing_products:

        existing_category = product[1]

        if existing_category.strip() == category:

            return HTMLResponse(
                f"""
                <script>

                    alert(
                        "❌ สินค้านี้มีอยู่แล้ว: {category}"
                    );

                    window.location.href="/products";

                </script>
                """
            )


    try:

        # ==================================
        # 1. สร้างสินค้า
        # ==================================

        product_id = add_product(
            category
        )


        # ==================================
        # 2. บันทึกราคาแต่ละไซส์
        # ==================================

        add_product_price(
            product_id,
            "S",
            cost_s,
            price_s
        )

        add_product_price(
            product_id,
            "M",
            cost_m,
            price_m
        )

        add_product_price(
            product_id,
            "L",
            cost_l,
            price_l
        )

        add_product_price(
            product_id,
            "XL",
            cost_xl,
            price_xl
        )

        add_product_price(
            product_id,
            "2XL",
            cost_2xl,
            price_2xl
        )

        add_product_price(
            product_id,
            "3XL",
            cost_3xl,
            price_3xl
        )


        # ==================================
        # 3. สร้าง Stock S-3XL
        # ==================================

        create_product_stock(
            category
        )


        # ==================================
        # 4. บันทึก Stock เริ่มต้น
        # ==================================

        stock_data = [

            ("S", stock_s),

            ("M", stock_m),

            ("L", stock_l),

            ("XL", stock_xl),

            ("2XL", stock_2xl),

            ("3XL", stock_3xl),

        ]


        conn = sqlite3.connect(
            DB_NAME
        )

        cursor = conn.cursor()


        for size, quantity in stock_data:

            cursor.execute(
                """
                UPDATE stock

                SET quantity=?

                WHERE category=?

                AND size=?
                """,
                (
                    quantity,
                    category,
                    size
                )
            )


        conn.commit()

        conn.close()


        # ==================================
        # สำเร็จ
        # ==================================

        return HTMLResponse(
            """
            <script>

                alert(
                    "✅ เพิ่มสินค้า + ราคา + Stock เรียบร้อยแล้ว"
                );

                window.location.href="/products";

            </script>
            """
        )


    except sqlite3.IntegrityError:

        return HTMLResponse(
            """
            <script>

                alert(
                    "❌ สินค้านี้มีอยู่แล้ว"
                );

                window.location.href="/products";

            </script>
            """
        )


    except Exception as e:

        print(
            "PRODUCT ADD ERROR:",
            e
        )

        return HTMLResponse(
            """
            <script>

                alert(
                    "❌ เกิดข้อผิดพลาดในการเพิ่มสินค้า"
                );

                window.location.href="/products";

            </script>
            """
        )


# ==========================================
# Update Price
# ==========================================

@router.post("/products/update-price")
def update_price(

    price_id: int = Form(...),

    cost: float = Form(...),

    price: float = Form(...)

):

    update_product_price(

        price_id,

        cost,

        price

    )

    return RedirectResponse(

        url="/products",

        status_code=303

    )


# ==========================================
# Delete Price By Size
# ==========================================

@router.post("/products/delete-price")
def delete_price(

    price_id: int = Form(...)

):

    delete_product_price(
        price_id
    )

    return RedirectResponse(

        url="/products",

        status_code=303

    )


# ==========================================
# Delete Product
# ==========================================

@router.post("/products/delete")
def remove_product(

    product_id: int = Form(...)

):

    delete_product(
        product_id
    )

    return RedirectResponse(

        url="/products",

        status_code=303

    )

# ==========================================
# Edit Product Name
# ==========================================

@router.post("/products/update")
def update_product(
    product_id: int = Form(...),
    category: str = Form(...)
):

    category = category.strip()

    # -------------------------------
    # ตรวจชื่อว่าง
    # -------------------------------

    if not category:

        return HTMLResponse(
            """
            <script>
                alert("❌ กรุณากรอกชื่อสินค้า");
                window.location.href="/products";
            </script>
            """
        )

    # -------------------------------
    # ตรวจชื่อซ้ำ
    # -------------------------------

    for product in get_products():

        existing_id = product[0]
        existing_name = product[1]

        if (
            existing_id != product_id
            and existing_name.strip() == category
        ):

            return HTMLResponse(
                f"""
                <script>
                    alert(
                        "❌ มีสินค้า '{category}' อยู่แล้ว"
                    );
                    window.location.href="/products";
                </script>
                """
            )

    # -------------------------------
    # แก้ชื่อ
    # -------------------------------

    success = update_product_name(
        product_id,
        category
    )

    if success:

        return HTMLResponse(
            """
            <script>
                alert("✅ แก้ชื่อสินค้าเรียบร้อย");
                window.location.href="/products";
            </script>
            """
        )

    return HTMLResponse(
        """
        <script>
            alert("❌ ไม่พบสินค้านี้");
            window.location.href="/products";
        </script>
        """
    )