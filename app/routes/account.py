import io
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import pandas as pd

from app.database.account_db import (
    add_transaction,
    clear_work_income,
    delete_transaction,
    get_account_summary,
    get_work_income_summary,
    update_transaction,
)

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/account", response_class=HTMLResponse)
def account_page(
    request: Request,
    scope: str = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    selected_month: Optional[str] = Query(None),
):
    current_time = datetime.now()
    
    # กำหนดค่าเดือนเริ่มต้น (ฟอร์แมต YYYY-MM เช่น "2026-08")
    if not selected_month:
        selected_month = current_time.strftime("%Y-%m")

    # หากเลือกหมวดชีวิตประจำวัน (personal) และไม่ได้กรองวันที่แบบกำหนดเอง
    # จะตัดยอดรายวันให้อัตโนมัติ (เฉพาะวันนี้)
    if scope == "personal" and not start_date and not end_date:
        today_str = current_time.strftime("%Y-%m-%d")
        summary = get_account_summary(
            selected_scope="personal", start_date=today_str, end_date=today_str
        )
    else:
        summary = get_account_summary(
            selected_scope=scope, start_date=start_date, end_date=end_date
        )

    # ดึงข้อมูลสรุปยอดรวมทั้งเดือนสำหรับหมวด Personal
    month_start = f"{selected_month}-01"
    # หาวันที่สุดท้ายของเดือน
    if selected_month.split("-")[1] in ["01", "03", "05", "07", "08", "10", "12"]:
        month_end = f"{selected_month}-31"
    elif selected_month.split("-")[1] in ["04", "06", "09", "11"]:
        month_end = f"{selected_month}-30"
    else:
        month_end = f"{selected_month}-29"

    monthly_summary = get_account_summary(
        selected_scope="personal", start_date=month_start, end_date=month_end
    )

    work_current_income = get_work_income_summary()

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "request": request,
            "summary": summary,
            "monthly_summary": monthly_summary,
            "selected_month": selected_month,
            "work_current_income": work_current_income,
            "start_date": start_date or "",
            "end_date": end_date or "",
        },
    )


# 📊 API ดาวน์โหลดไฟล์ Excel
@router.get("/api/account/export-excel")
def export_excel(
    scope: str = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    summary = get_account_summary(
        selected_scope=scope, start_date=start_date, end_date=end_date
    )
    transactions = summary.get("transactions", [])

    formatted_data = []
    for item in transactions:
        formatted_data.append(
            {
                "ID": item[0],
                "รายการ": item[1],
                "ประเภท": "รายรับ" if item[2] == "income" else "รายจ่าย",
                "จำนวนเงิน (บาท)": item[3],
                "หมวดหมู่": item[4],
                "วัน-เวลา": item[5],
                "บัญชี": (
                    "งาน/ร้านค้า" if item[6] == "work" else "ชีวิตประจำวัน"
                ),
            }
        )

    df = pd.DataFrame(formatted_data)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary_Report")
    output.seek(0)

    filename = f"account_report_{scope}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}

    return StreamingResponse(
        output,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.post("/api/account/add")
def add_account_item(
    title: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    category: str = Form("ทั่วไป"),
    scope: str = Form("personal"),
):
    add_transaction(title, type, amount, category, scope)
    return RedirectResponse(
        url=f"/account?scope={scope}", status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/api/account/delete/{trans_id}")
def delete_account_item(trans_id: int, current_scope: str = Form("all")):
    delete_transaction(trans_id)
    return RedirectResponse(
        url=f"/account?scope={current_scope}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/api/account/update/{trans_id}")
def update_account_item(
    trans_id: int,
    title: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    category: str = Form("ทั่วไป"),
    scope: str = Form("personal"),
    current_scope: str = Form("all"),
):
    update_transaction(trans_id, title, type, amount, category, scope)
    return RedirectResponse(
        url=f"/account?scope={current_scope}",
        status_code=status.HTTP_303_SEE_OTHER,
    )


@router.post("/api/account/clear-work-income")
def clear_work_income_route():
    try:
        clear_work_income()
    except Exception as e:
        print(f"Error clearing work income: {e}")
    return RedirectResponse(
        url="/account?scope=work", status_code=status.HTTP_303_SEE_OTHER
    )