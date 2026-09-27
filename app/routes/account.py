import io
from datetime import datetime, timedelta, timezone
from calendar import monthrange
from typing import Optional

import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from fastapi import APIRouter, Form, Query, Request, status
from fastapi.responses import (
    HTMLResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.templating import Jinja2Templates

from app.database.account_db import (
    get_db_connection,
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
    scope: str = Query("personal"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    selected_month: Optional[str] = Query(None),
):
    current_time = datetime.now(tz_thai)

    # --------------------------------------
    # ตรวจสอบ Scope
    # --------------------------------------
    valid_scopes = {"all", "personal", "work"}
    if scope not in valid_scopes:
        scope = "personal"

    # --------------------------------------
    # 1. กำหนดวันปัจจุบันเสมอถ้าผู้ใช้ไม่ได้เลือกวัน
    # --------------------------------------
    if not start_date:
        start_date = current_time.strftime("%Y-%m-%d")

    if not end_date:
        end_date = start_date

    # --------------------------------------
    # 2. กำหนดเดือนปัจจุบันถ้าไม่ได้เลือก
    # --------------------------------------
    if not selected_month:
        selected_month = current_time.strftime("%Y-%m")

    # --------------------------------------
    # 3. คำนวณช่วงวันของเดือนที่เลือก
    # --------------------------------------
    try:
        year, month = map(int, selected_month.split("-"))
        datetime(year=year, month=month, day=1)
    except (ValueError, AttributeError, TypeError):
        year = current_time.year
        month = current_time.month
        selected_month = f"{year:04d}-{month:02d}"

    last_day = monthrange(year, month)[1]
    month_start = f"{year:04d}-{month:02d}-01"
    month_end = f"{year:04d}-{month:02d}-{last_day:02d}"

    # --------------------------------------
    # เปิด Connection เดียวใช้งานร่วมกันตลอด Request
    # --------------------------------------
    conn = get_db_connection()

    try:
        # 4. ดึงสรุปยอดรายวัน (Daily)
        summary = get_account_summary(
            selected_scope=scope,
            start_date=start_date,
            end_date=end_date,
            conn=conn
        )

        # 5. ดึงสรุปยอดรายเดือน (Monthly) โดยใช้ Connection เดิม
        monthly_summary = get_account_summary(
            selected_scope=scope,
            start_date=month_start,
            end_date=month_end,
            conn=conn
        )

        # 6. กรณีเลือก Scope เป็น Work
        work_current_income = 0.0
        if scope == "work":
            work_current_income = float(summary.get("work_current_income") or 0)

        # --------------------------------------
        # RETURN TEMPLATE
        # --------------------------------------
        return templates.TemplateResponse(
            request=request,
            name="account.html",
            context={
                "request": request,
                "scope": scope,
                "summary": summary,
                "monthly_summary": monthly_summary,
                "selected_month": selected_month,
                "work_current_income": work_current_income,
                "start_date": start_date or "",
                "end_date": end_date or "",
            },
        )
    finally:
        # ปิด Connection หลังการดึงข้อมูลเสร็จสมบูรณ์
        conn.close()


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
    period: str = Query("daily"),
    selected_month: Optional[str] = Query(None),
):

    valid_scopes = {"all", "personal", "work"}
    if scope not in valid_scopes:
        scope = "all"

    if period not in {"daily", "monthly"}:
        period = "daily"

    if period == "monthly":
        current_time = datetime.now(tz_thai)

        if not selected_month:
            selected_month = current_time.strftime("%Y-%m")

        try:
            selected_month_date = datetime.strptime(selected_month, "%Y-%m")
            year = selected_month_date.year
            month = selected_month_date.month
        except (ValueError, TypeError):
            year = current_time.year
            month = current_time.month
            selected_month = current_time.strftime("%Y-%m")

        last_day = monthrange(year, month)[1]
        start_date = f"{year:04d}-{month:02d}-01"
        end_date = f"{year:04d}-{month:02d}-{last_day:02d}"

    if start_date and not end_date:
        end_date = start_date

    # --------------------------------------
    # ดึงข้อมูลผ่าน Connection เดียว
    # --------------------------------------
    conn = get_db_connection()
    try:
        summary = get_account_summary(
            selected_scope=scope,
            start_date=start_date,
            end_date=end_date,
            transaction_limit=None,
            conn=conn
        )
    finally:
        conn.close()

    transactions = summary.get("transactions", []) or []

    formatted_data = []
    for item in transactions:
        formatted_data.append(
            {
                "ID": item[0],
                "รายการ": item[1],
                "ประเภท": ("รายรับ" if item[2] == "income" else "รายจ่าย"),
                "จำนวนเงิน (บาท)": float(item[3]),
                "หมวดหมู่": item[4],
                "วัน-เวลา": item[5],
                "บัญชี": ("งาน/ร้านค้า" if item[6] == "work" else "ชีวิตประจำวัน"),
            }
        )

    excel_columns = [
        "ID",
        "รายการ",
        "ประเภท",
        "จำนวนเงิน (บาท)",
        "หมวดหมู่",
        "วัน-เวลา",
        "บัญชี",
    ]

    df = pd.DataFrame(formatted_data, columns=excel_columns)

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Summary_Report")
        ws = writer.sheets["Summary_Report"]

        # --------------------------------------
        # 1. ❄️ ล็อกแถวหัวข้อ (Freeze Header Row)
        # --------------------------------------
        ws.freeze_panes = "A2"
        ws.views.sheetView[0].showGridLines = True

        # Styles definition
        header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid")
        row_fill_even = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
        
        align_center = Alignment(horizontal="center", vertical="center")
        align_left = Alignment(horizontal="left", vertical="center")
        align_right = Alignment(horizontal="right", vertical="center")
        
        thin_border = Border(
            left=Side(style="thin", color="CBD5E1"),
            right=Side(style="thin", color="CBD5E1"),
            top=Side(style="thin", color="CBD5E1"),
            bottom=Side(style="thin", color="CBD5E1")
        )

        # --------------------------------------
        # 2. 🎨 ตกแต่ง Header Row (แถวที่ 1)
        # --------------------------------------
        ws.row_dimensions[1].height = 28
        for cell in ws[1]:
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = align_center
            cell.border = thin_border

        # --------------------------------------
        # 3. 📝 ตกแต่ง Data Rows (แถวที่ 2 เป็นต้นไป)
        # --------------------------------------
        for row_idx in range(2, ws.max_row + 1):
            ws.row_dimensions[row_idx].height = 22
            is_even = (row_idx % 2 == 0)

            for col_idx in range(1, ws.max_column + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.border = thin_border
                
                if is_even:
                    cell.fill = row_fill_even

                col_name = excel_columns[col_idx - 1]
                if col_name in ["ID", "ประเภท", "วัน-เวลา", "บัญชี"]:
                    cell.alignment = align_center
                elif col_name == "จำนวนเงิน (บาท)":
                    cell.alignment = align_right
                    cell.number_format = "#,##0.00"
                else:
                    cell.alignment = align_left

        # --------------------------------------
        # 4. 📐 ปรับความกว้างคอลัมน์อัตโนมัติ (Auto Width)
        # --------------------------------------
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or "")
                # เพิ่มน้ำหนักการคำนวณภาษาไทยเพื่อความแม่นยำ
                length = sum(2 if ord(char) > 127 else 1 for char in val_str)
                max_len = max(max_len, length)
            
            ws.column_dimensions[col_letter].width = max(max_len + 5, 12)

    output.seek(0)

    if period == "monthly" and selected_month:
        safe_selected_month = selected_month.replace("/", "-")
        filename = f"account_report_{scope}_monthly_{safe_selected_month}.xlsx"
    else:
        filename = f"account_report_{scope}_{datetime.now(tz_thai).strftime('%Y%m%d_%H%M')}.xlsx"

    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }

    return StreamingResponse(
        output,
        headers=headers,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
    if scope not in {"personal", "work"}:
        scope = "personal"

    conn = get_db_connection()
    try:
        add_transaction(
            title=title,
            trans_type=type,
            amount=amount,
            category=category,
            scope=scope,
            conn=conn
        )
    finally:
        conn.close()

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
    if current_scope not in {"all", "personal", "work"}:
        current_scope = "all"

    conn = get_db_connection()
    try:
        delete_transaction(trans_id, conn=conn)
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/account?scope={current_scope}",
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
    if scope not in {"personal", "work"}:
        scope = "personal"

    if current_scope not in {"all", "personal", "work"}:
        current_scope = "all"

    conn = get_db_connection()
    try:
        update_transaction(
            trans_id=trans_id,
            title=title,
            trans_type=type,
            amount=amount,
            category=category,
            scope=scope,
            conn=conn
        )
    finally:
        conn.close()

    return RedirectResponse(
        url=f"/account?scope={current_scope}",
        status_code=status.HTTP_303_SEE_OTHER
    )


# ==========================================
# CLEAR WORK INCOME
# ==========================================

@router.post(
    "/api/account/clear-work-income"
)
def clear_work_income_route():
    conn = get_db_connection()
    try:
        clear_work_income(conn=conn)
    except Exception as e:
        print("Error clearing work income:", e)
    finally:
        conn.close()

    return RedirectResponse(
        url="/account?scope=work",
        status_code=status.HTTP_303_SEE_OTHER
    )