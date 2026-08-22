from fastapi import APIRouter, Request, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from app.database.account_db import (
    add_transaction, 
    get_account_summary, 
    delete_transaction, 
    update_transaction,
    clear_work_income,
    get_work_income_summary  # ✨ ดึงฟังก์ชันคำนวณยอดงานรอบปัจจุบันเพิ่มเข้ามา
)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()

@router.get("/account", response_class=HTMLResponse)
def account_page(request: Request, scope: str = Query("all")):
    summary = get_account_summary(selected_scope=scope)
    
    # ✨ ดึงยอดรายรับงานรอบปัจจุบัน (ที่ยังไม่เคลียร์) ส่งไปให้ Template
    work_current_income = get_work_income_summary()

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "request": request, 
            "summary": summary,
            "work_current_income": work_current_income  # ✨ ส่งค่ายอดกล่องสีเขียวไปที่หน้า HTML
        }
    )

@router.post("/api/account/add")
def add_account_item(
    title: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    category: str = Form("ทั่วไป"),
    scope: str = Form("personal")
):
    add_transaction(title, type, amount, category, scope)
    return RedirectResponse(url=f"/account?scope={scope}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/account/delete/{trans_id}")
def delete_account_item(trans_id: int, current_scope: str = Form("all")):
    delete_transaction(trans_id)
    return RedirectResponse(url=f"/account?scope={current_scope}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/account/update/{trans_id}")
def update_account_item(
    trans_id: int,
    title: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    category: str = Form("ทั่วไป"),
    scope: str = Form("personal"),
    current_scope: str = Form("all")
):
    update_transaction(trans_id, title, type, amount, category, scope)
    return RedirectResponse(url=f"/account?scope={current_scope}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/api/account/clear-work-income")
def clear_work_income_route():
    try:
        clear_work_income()
    except Exception as e:
        print(f"Error clearing work income: {e}")
    return RedirectResponse(url="/account?scope=work", status_code=status.HTTP_303_SEE_OTHER)