from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database.account_db import add_transaction, get_transactions

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request):
    items = get_transactions()
    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={"request": request, "items": items}
    )

@router.post("/api/account/add")
def add_account_item(title: str = Form(...), type: str = Form(...), amount: float = Form(...), category: str = Form("ทั่วไป")):
    add_transaction(title, type, amount, category)
    return RedirectResponse(url="/account", status_code=303)