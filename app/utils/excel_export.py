import os
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from app.database.db import get_db_connection


def create_excel(event_name="", date=""):

    os.makedirs(
        "exports",
        exist_ok=True
    )

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            event_name = event_name.strip()
            target_date = date.strip() if date else ""

            # ==========================================
            # สร้างคำสั่ง SQL ดึงข้อมูลรายการขาย
            # ==========================================
            sql_rows = """
                SELECT
                    created_at,
                    event_name,
                    category,
                    size,
                    cost,
                    price,
                    profit,
                    COALESCE(payment_method, 'เงินสด') as payment_method
                FROM sales
                WHERE 1=1
            """
            params_rows = []

            if event_name:
                sql_rows += " AND TRIM(event_name) = TRIM(%s)"
                params_rows.append(event_name)

            if target_date:
                sql_rows += " AND DATE(created_at) = %s"
                params_rows.append(target_date)

            sql_rows += " ORDER BY id DESC"

            cursor.execute(sql_rows, tuple(params_rows))
            raw_rows = cursor.fetchall()

            # แปลงข้อมูลให้อยู่ในรูปแบบ tuple สำหรับเขียนลง Excel
            rows = []
            for r in raw_rows:
                if isinstance(r, dict):
                    rows.append((
                        str(r.get("created_at", "")),
                        r.get("event_name", ""),
                        r.get("category", ""),
                        r.get("size", ""),
                        float(r.get("cost") or 0),
                        float(r.get("price") or 0),
                        float(r.get("profit") or 0),
                        r.get("payment_method", "เงินสด")
                    ))
                else:
                    rows.append(r)

            # ==========================================
            # สรุปยอด (แก้เครื่องหมาย % เป็น %% สำหรับ PyMySQL)
            # ==========================================
            sql_summary = """
                SELECT
                    COUNT(*),
                    COALESCE(SUM(price), 0),
                    COALESCE(SUM(cost), 0),
                    COALESCE(SUM(profit), 0),
                    COALESCE(SUM(CASE WHEN LOWER(payment_method) LIKE '%%cash%%' OR payment_method = 'เงินสด' THEN price ELSE 0 END), 0) as cash_total,
                    COALESCE(SUM(CASE WHEN LOWER(payment_method) LIKE '%%transfer%%' OR payment_method = 'โอนเงิน' OR payment_method = 'โอน' THEN price ELSE 0 END), 0) as transfer_total,
                    COALESCE(SUM(CASE WHEN LOWER(payment_method) LIKE '%%half%%' OR payment_method = 'คนละครึ่ง' THEN price ELSE 0 END), 0) as half_total
                FROM sales
                WHERE 1=1
            """
            params_summary = []

            if event_name:
                sql_summary += " AND TRIM(event_name) = TRIM(%s)"
                params_summary.append(event_name)

            if target_date:
                sql_summary += " AND DATE(created_at) = %s"
                params_summary.append(target_date)

            cursor.execute(sql_summary, tuple(params_summary))
            summary = cursor.fetchone()

    finally:
        conn.close()

    if isinstance(summary, dict):
        qty = float(summary.get("COUNT(*)") or summary.get("count") or 0)
        sales = float(summary.get("COALESCE(SUM(price), 0)") or summary.get("sales") or 0)
        cost = float(summary.get("COALESCE(SUM(cost), 0)") or summary.get("cost") or 0)
        profit = float(summary.get("COALESCE(SUM(profit), 0)") or summary.get("profit") or 0)
        cash_total = float(summary.get("cash_total") or 0)
        transfer_total = float(summary.get("transfer_total") or 0)
        half_total = float(summary.get("half_total") or 0)
    else:
        qty = summary[0] or 0
        sales = summary[1] or 0
        cost = summary[2] or 0
        profit = summary[3] or 0
        cash_total = float(summary[4] or 0) if len(summary) > 4 else 0
        transfer_total = float(summary[5] or 0) if len(summary) > 5 else 0
        half_total = float(summary[6] or 0) if len(summary) > 6 else 0

    # ==========================================
    # สร้าง Excel
    # ==========================================

    wb = Workbook()
    ws = wb.active
    ws.title = "Sales"

    # ==========================================
    # หัวรายงาน
    # ==========================================

    ws.merge_cells("A1:H1")
    ws["A1"] = "MAXKY POS"
    ws["A1"].font = Font(size=20, bold=True)
    ws["A1"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # ==========================================
    # ชื่องาน / วันที่
    # ==========================================

    ws.merge_cells("A2:H2")

    title_parts = []
    if event_name:
        title_parts.append(f"ชื่องาน : {event_name}")
    else:
        title_parts.append("รายงานยอดขาย : ทุกงาน")

    if target_date:
        title_parts.append(f"วันที่ : {target_date}")

    ws["A2"] = " | ".join(title_parts)
    ws["A2"].font = Font(size=14, bold=True)
    ws["A2"].alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 25

    # ==========================================
    # สรุปยอด
    # ==========================================

    ws["A4"] = "จำนวนขาย"
    ws["B4"] = qty
    ws["C4"] = "ตัว"

    ws["D4"] = "ยอดขาย"
    ws["E4"] = sales
    ws["F4"] = "บาท"

    ws["A5"] = "ต้นทุน"
    ws["B5"] = cost
    ws["C5"] = "บาท"

    ws["D5"] = "กำไร"
    ws["E5"] = profit
    ws["F5"] = "บาท"

    ws["A6"] = "💵 เงินสด"
    ws["B6"] = cash_total
    ws["C6"] = "บาท"

    ws["D6"] = "📱 โอนเงิน"
    ws["E6"] = transfer_total
    ws["F6"] = "บาท"

    ws["A7"] = "🤝 คนละครึ่ง"
    ws["B7"] = half_total
    ws["C7"] = "บาท"

    # ==========================================
    # Style สรุป
    # ==========================================

    summary_fill = PatternFill("solid", fgColor="E8F5E9")
    thin = Side(style="thin", color="D9D9D9")
    summary_border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for row in ws.iter_rows(min_row=4, max_row=7, min_col=1, max_col=6):
        for cell in row:
            cell.fill = summary_fill
            cell.border = summary_border
            cell.alignment = Alignment(vertical="center")

    for cell in ["A4", "D4", "A5", "D5", "A6", "D6", "A7"]:
        ws[cell].font = Font(bold=True)

    for cell in ["B4", "E4", "B5", "E5", "B6", "E6", "B7"]:
        ws[cell].font = Font(size=12, bold=True)

    # ==========================================
    # รูปแบบตัวเลข
    # ==========================================

    ws["B4"].number_format = '#,##0'
    ws["E4"].number_format = '#,##0.00'
    ws["B5"].number_format = '#,##0.00'
    ws["E5"].number_format = '#,##0.00'
    ws["B6"].number_format = '#,##0.00'
    ws["E6"].number_format = '#,##0.00'
    ws["B7"].number_format = '#,##0.00'

    # ==========================================
    # เว้นบรรทัด
    # ==========================================

    ws["A9"] = "รายละเอียดการขาย"
    ws["A9"].font = Font(size=14, bold=True)

    # ==========================================
    # Header ตาราง
    # ==========================================

    ws.append([])
    ws.append(["วันที่", "ชื่องาน", "สินค้า", "ไซส์", "ต้นทุน", "ราคาขาย", "กำไร", "ช่องทางชำระ"])

    header_row = 11
    header_fill = PatternFill("solid", fgColor="DDEBF7")

    for cell in ws[header_row]:
        cell.font = Font(bold=True)
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = summary_border

    # ==========================================
    # Data
    # ==========================================

    for row in rows:
        ws.append(row)

    # ==========================================
    # จัดรูปแบบข้อมูล
    # ==========================================

    for row in ws.iter_rows(min_row=12, max_row=ws.max_row, min_col=1, max_col=8):
        for cell in row:
            cell.border = Border(bottom=Side(style="hair", color="DDDDDD"))
            cell.alignment = Alignment(vertical="center")

    for row in range(12, ws.max_row + 1):
        ws[f"E{row}"].number_format = '#,##0.00'
        ws[f"F{row}"].number_format = '#,##0.00'
        ws[f"G{row}"].number_format = '#,##0.00'

    # ==========================================
    # ความกว้างคอลัมน์
    # ==========================================

    ws.column_dimensions["A"].width = 20
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 10
    ws.column_dimensions["E"].width = 12
    ws.column_dimensions["F"].width = 12
    ws.column_dimensions["G"].width = 12
    ws.column_dimensions["H"].width = 16

    ws.freeze_panes = "A12"

    # ==========================================
    # ชื่อไฟล์
    # ==========================================

    name_parts = []
    if event_name:
        safe_name = "".join(c for c in event_name if c not in '\\/:*?"<>|').strip()
        name_parts.append(safe_name)

    if target_date:
        name_parts.append(target_date)

    if name_parts:
        filename = f"exports/MAXKY_{'_'.join(name_parts)}.xlsx"
    else:
        filename = "exports/MAXKY_SALES.xlsx"

    wb.save(filename)

    return filename