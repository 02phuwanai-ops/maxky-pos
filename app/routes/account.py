import io
from datetime import datetime, timedelta, timezone
from calendar import monthrange
from typing import Optional

import pandas as pd
from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates

from app.database.account_db import (
    add_transaction,
    clear_work_income,
    delete_transaction,
    get_account_summary,
    update_transaction,
)


# ==========================================
# TIMEZONE ประเทศไทย UTC+7
# ==========================================

tz_thai = timezone(timedelta(hours=7))


# ==========================================
# TEMPLATE / ROUTER
# ==========================================

templates = Jinja2Templates(
    directory="app/templates"
)

router = APIRouter()


# ==========================================
# ACCOUNT PAGE
# ==========================================

@router.get(
    "/account",
    response_class=HTMLResponse
)
def account_page(
    request: Request,
    scope: str = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    selected_month: Optional[str] = Query(None),
):

    current_time = datetime.now(tz_thai)

    # ==========================================
    # ตรวจสอบ Scope
    # ==========================================

    valid_scopes = {
        "all",
        "personal",
        "work",
    }

    if scope not in valid_scopes:
        scope = "all"

    # ==========================================
    # กำหนดเดือนปัจจุบัน
    # ==========================================

    if not selected_month:

        selected_month = current_time.strftime(
            "%Y-%m"
        )

    # ==========================================
    # ตัวแปรเริ่มต้น
    # ==========================================

    monthly_summary = None
    work_current_income = 0.0

    # ==========================================
    # PERSONAL
    # ==========================================

    if scope == "personal":

        # --------------------------------------
        # ถ้าไม่ได้เลือกวัน
        # แสดงข้อมูลของวันนี้
        # --------------------------------------

        if not start_date:

            start_date = current_time.strftime(
                "%Y-%m-%d"
            )

        # --------------------------------------
        # ถ้าไม่ได้เลือกวันสิ้นสุด
        # ใช้วันเดียวกับวันเริ่มต้น
        # --------------------------------------

        if not end_date:

            end_date = start_date

        # --------------------------------------
        # ดึงข้อมูลของวัน
        # --------------------------------------

        summary = get_account_summary(
            selected_scope="personal",
            start_date=start_date,
            end_date=end_date
        )

        # --------------------------------------
        # ตรวจสอบเดือน
        # --------------------------------------

        try:

            year, month = map(
                int,
                selected_month.split("-")
            )

        except (
            ValueError,
            AttributeError
        ):

            year = current_time.year
            month = current_time.month

            selected_month = (
                f"{year:04d}-{month:02d}"
            )

        # --------------------------------------
        # หาวันสุดท้ายของเดือน
        # รองรับเดือนกุมภาพันธ์ / Leap Year
        # --------------------------------------

        last_day = monthrange(
            year,
            month
        )[1]

        month_start = (
            f"{year:04d}-{month:02d}-01"
        )

        month_end = (
            f"{year:04d}-{month:02d}-"
            f"{last_day:02d}"
        )

        # --------------------------------------
        # ดึงสรุปยอดทั้งเดือน
        # --------------------------------------

        monthly_summary = get_account_summary(
            selected_scope="personal",
            start_date=month_start,
            end_date=month_end
        )

    # ==========================================
    # WORK
    # ==========================================

    elif scope == "work":

        # --------------------------------------
        # ถ้าเลือกเพียงวันเดียว
        # ให้สิ้นสุดวันเดียวกัน
        # --------------------------------------

        if start_date and not end_date:

            end_date = start_date

        # --------------------------------------
        # ดึงข้อมูล Work
        # --------------------------------------

        summary = get_account_summary(
            selected_scope="work",
            start_date=start_date,
            end_date=end_date
        )

        # --------------------------------------
        # ใช้ยอด Work ที่ get_account_summary()
        # ดึงมาให้แล้ว ไม่ต้องเปิด DB เพิ่ม
        # --------------------------------------

        work_current_income = float(
            summary.get(
                "work_current_income"
            ) or 0
        )

    # ==========================================
    # ALL
    # ==========================================

    else:

        # --------------------------------------
        # ถ้าเลือกวันเดียว
        # ให้สิ้นสุดวันเดียวกัน
        # --------------------------------------

        if start_date and not end_date:

            end_date = start_date

        # --------------------------------------
        # ดึงข้อมูลทั้งหมด
        # --------------------------------------

        summary = get_account_summary(
            selected_scope="all",
            start_date=start_date,
            end_date=end_date
        )

    # ==========================================
    # RETURN TEMPLATE
    # ==========================================

    return templates.TemplateResponse(
        request=request,
        name="account.html",
        context={

            "request": request,

            # ----------------------------------
            # Scope ปัจจุบัน
            # ----------------------------------

            "scope": scope,

            # ----------------------------------
            # ข้อมูลหน้าหลัก
            # ----------------------------------

            "summary": summary,

            # ----------------------------------
            # Personal รายเดือน
            # ----------------------------------

            "monthly_summary": monthly_summary,

            "selected_month": selected_month,

            # ----------------------------------
            # Work
            # ----------------------------------

            "work_current_income": (
                work_current_income
            ),

            # ----------------------------------
            # วันที่สำหรับ Filter
            # ----------------------------------

            "start_date": (
                start_date or ""
            ),

            "end_date": (
                end_date or ""
            ),
        },
    )


# ==========================================
# EXPORT EXCEL
# ==========================================

@router.get(
    "/api/account/export-excel"
)
def export_excel(
    scope: str = Query("all"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):

    # ==========================================
    # ตรวจสอบ Scope
    # ==========================================

    valid_scopes = {
        "all",
        "personal",
        "work",
    }

    if scope not in valid_scopes:

        scope = "all"

    # ==========================================
    # ถ้าเลือกวันเดียว
    # ==========================================

    if start_date and not end_date:

        end_date = start_date

    # ==========================================
    # ดึงข้อมูล
    # ==========================================

    summary = get_account_summary(
        selected_scope=scope,
        start_date=start_date,
        end_date=end_date
    )

    # สำคัญ:
    # กำหนด transactions ก่อนนำไปใช้
    transactions = summary.get(
        "transactions",
        []
    )

    # ==========================================
    # จัดรูปแบบข้อมูล Excel
    # ==========================================

    formatted_data = []

    for item in transactions:

        formatted_data.append(
            {
                "ID": item[0],

                "รายการ": item[1],

                "ประเภท": (
                    "รายรับ"
                    if item[2] == "income"
                    else "รายจ่าย"
                ),

                "จำนวนเงิน (บาท)": float(
                    item[3]
                ),

                "หมวดหมู่": item[4],

                "วัน-เวลา": item[5],

                "บัญชี": (
                    "งาน/ร้านค้า"
                    if item[6] == "work"
                    else "ชีวิตประจำวัน"
                ),
            }
        )

    # ==========================================
    # สร้าง DataFrame
    # ==========================================

    df = pd.DataFrame(
        formatted_data
    )

    # ==========================================
    # สร้าง Excel ใน Memory
    # ==========================================

    output = io.BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Summary_Report"
        )

    output.seek(0)

    # ==========================================
    # ชื่อไฟล์
    # ==========================================

    filename = (
        f"account_report_{scope}_"
        f"{datetime.now(tz_thai).strftime('%Y%m%d_%H%M')}"
        f".xlsx"
    )

    headers = {
        "Content-Disposition": (
            f'attachment; filename="{filename}"'
        )
    }

    # ==========================================
    # RETURN FILE
    # ==========================================

    return StreamingResponse(
        output,
        headers=headers,
        media_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
    )


# ==========================================
# ADD TRANSACTION
# ==========================================

@router.post(
    "/api/account/add"
)
def add_account_item(
    title: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    category: str = Form("ทั่วไป"),
    scope: str = Form("personal"),
):

    # ==========================================
    # ตรวจสอบ Scope
    # ==========================================

    if scope not in {
        "personal",
        "work",
    }:

        scope = "personal"

    # ==========================================
    # เพิ่มข้อมูล
    # ==========================================

    add_transaction(
        title=title,
        trans_type=type,
        amount=amount,
        category=category,
        scope=scope
    )

    # ==========================================
    # Redirect
    # ==========================================

    return RedirectResponse(
        url=f"/account?scope={scope}",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ==========================================
# DELETE TRANSACTION
# ==========================================

@router.post(
    "/api/account/delete/{trans_id}"
)
def delete_account_item(
    trans_id: int,
    current_scope: str = Form("all"),
):

    # ==========================================
    # ตรวจสอบ Scope
    # ==========================================

    if current_scope not in {
        "all",
        "personal",
        "work",
    }:

        current_scope = "all"

    # ==========================================
    # ลบข้อมูล
    # ==========================================

    delete_transaction(
        trans_id
    )

    # ==========================================
    # Redirect
    # ==========================================

    return RedirectResponse(
        url=(
            f"/account?"
            f"scope={current_scope}"
        ),
        status_code=status.HTTP_303_SEE_OTHER
    )


# ==========================================
# UPDATE TRANSACTION
# ==========================================

@router.post(
    "/api/account/update/{trans_id}"
)
def update_account_item(
    trans_id: int,
    title: str = Form(...),
    type: str = Form(...),
    amount: float = Form(...),
    category: str = Form("ทั่วไป"),
    scope: str = Form("personal"),
    current_scope: str = Form("all"),
):

    # ==========================================
    # ตรวจสอบ Scope ของรายการ
    # ==========================================

    if scope not in {
        "personal",
        "work",
    }:

        scope = "personal"

    # ==========================================
    # ตรวจสอบ Scope หน้าปัจจุบัน
    # ==========================================

    if current_scope not in {
        "all",
        "personal",
        "work",
    }:

        current_scope = "all"

    # ==========================================
    # แก้ไขข้อมูล
    # ==========================================

    update_transaction(
        trans_id=trans_id,
        title=title,
        trans_type=type,
        amount=amount,
        category=category,
        scope=scope
    )

    # ==========================================
    # Redirect
    # ==========================================

    return RedirectResponse(
        url=(
            f"/account?"
            f"scope={current_scope}"
        ),
        status_code=status.HTTP_303_SEE_OTHER
    )


# ==========================================
# CLEAR WORK INCOME
# ==========================================

@router.post(
    "/api/account/clear-work-income"
)
def clear_work_income_route():

    try:

        clear_work_income()

    except Exception as e:

        print(
            "Error clearing work income:",
            e
        )

    return RedirectResponse(
        url="/account?scope=work",
        status_code=status.HTTP_303_SEE_OTHER
    )