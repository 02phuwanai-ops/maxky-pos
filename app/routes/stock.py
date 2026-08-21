from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.database.stock_view_db import get_stock_all


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


@router.get(
    "/stock",
    response_class=HTMLResponse
)
def stock_page(request: Request):

    stocks = get_stock_all()

    products = {}

    for category, size, qty in stocks:

        if category not in products:

            products[category] = {
                "total": 0,
                "items": []
            }

        products[category]["total"] += qty

        products[category]["items"].append({
            "size": size,
            "quantity": qty
        })

    return templates.TemplateResponse(
        request=request,
        name="stock.html",
        context={
            "request": request,
            "products": products
        }
    )

@router.get("/api/stock")
def stock_api():

    stocks = get_stock_all()

    products = {}

    for category, size, qty in stocks:

        if category not in products:

            products[category] = {
                "total": 0,
                "items": []
            }

        products[category]["total"] += qty

        products[category]["items"].append({
            "size": size,
            "quantity": qty
        })

    return {
        "success": True,
        "products": products
    }