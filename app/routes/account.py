import io
import urllib.parse
import urllib.request
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

# 🔑 ใส่ Token ของ LINE Notify ของคุณตรงนี้
LINE_NOTIFY_TOKEN = "YOUR_LINE_NOTIFY_TOKEN"


@router.get("/account", response_class=HTMLResponse)
def account_page(
    request: Request,
    scope: str = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    summary = get_account_summary(
        selected_scope=scope, start_date=start_date, end_date=end_date
    )
    work_current_income = get_work_income_summary()

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={
            "request": request,
            "summary": summary,
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


# 💬 API ส่งสรุปยอดเข้า LINE (ตัด requests ออก ใช้ urllib แทน)
@router.post("/api/account/send-line")
def send_line_report(
    scope: str = Form("all"),
    income: float = Form(0.0),
    expense: float = Form(0.0),
    balance: float = Form(0.0),
):
    scope_name = (
        "ทั้งหมด"
        if scope == "all"
        else ("ชีวิตประจำวัน" if scope == "personal" else "งาน / ร้านค้า")
    )

    message = (
        f"\n📊 สรุปยอดบัญชี ({scope_name})\n"
        f"🟢 รายรับรวม: ฿{income:,.2f}\n"
        f"🔴 รายจ่ายรวม: ฿{expense:,.2f}\n"
        f"💰 คงเหลือสุทธิ: ฿{balance:,.2f}\n"
        f"-------------------\n"
        f"⏰ ข้อมูล ณ วันที่: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    url = "https://notify-api.line.me/api/notify"
    headers = {
        "Authorization": f"Bearer {LINE_NOTIFY_TOKEN}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = urllib.parse.urlencode({"message": message}).encode("utf-8")

    try:
        req = urllib.request.Request(
            url, data=data, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req) as response:
            pass
    except Exception as e:
        print(f"Error sending LINE Notify: {e}")

    return RedirectResponse(
        url=f"/account?scope={scope}", status_code=status.HTTP_303_SEE_OTHER
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