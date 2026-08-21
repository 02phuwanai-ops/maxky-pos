from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates


from app.database.dashboard_db import (
    get_dashboard,
    get_stock_count,
    get_low_stock_count,
    get_low_stock_items,
    get_top_product,
    get_top_sales
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



# ==========================================
# Build 0.81
# Dashboard Stock API
# ==========================================


@router.get("/api/dashboard-stock")
def dashboard_stock():


    return JSONResponse({

        "total":
        get_total_stock(),


        "stock":
        get_stock_groups()

    })



# ==========================================
# Build 0.82
# Group Stock API
# ==========================================


@router.get("/api/stock-group")
def stock_group():


    groups = get_stock_groups()


    return JSONResponse({

        "groups": groups

    })