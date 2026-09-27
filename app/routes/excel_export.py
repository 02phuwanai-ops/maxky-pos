import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# นำเข้าฟังก์ชันดึงข้อมูลยอดขายของคุณตามเดิม
# from app.database.sales_db import get_sales_report_data

def create_excel(event_name: str = ""):
    # 1. ดึงข้อมูลยอดขาย (ตัวอย่าง)
    # data = get_sales_report_data(event_name)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    # 2. กำหนด Header
    headers = ["ลำดับ", "วัน-เวลา", "หมวดหมู่/รายการ", "ไซส์", "ราคา (บาท)", "ช่องทางการชำระ", "จุดขาย/งาน"]
    ws.append(headers)

    # 3. ใส่ข้อมูลตัวอย่าง (หรือวนลูปใส่ข้อมูลจาก DB)
    # for idx, item in enumerate(data, 1):
    #     ws.append([idx, item['date'], item['category'], item['size'], item['price'], item['payment_method'], item['event_name']])

    # ----------------------------------------------------
    # 🎨 4. จัดสไตล์ให้สวยงาม + ล็อกแถวหัวข้อ
    # ----------------------------------------------------
    # ❄️ ล็อกแถวที่ 1 ไว้ ไม่ให้เลื่อนตามเมื่อ Scroll
    ws.freeze_panes = "A2"
    ws.views.sheetView[0].showGridLines = True

    # นิยามรูปแบบ Font และ สี
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="1E293B", end_color="1E293B", fill_type="solid") # สีกรมท่าเข้ม
    row_fill_even = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid") # สีแถวสลับ
    
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")
    
    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1")
    )

    # ตกแต่ง Header Row (แถวที่ 1)
    ws.row_dimensions[1].height = 28
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center
        cell.border = thin_border

    # ตกแต่ง Data Rows (แถวที่ 2 เป็นต้นไป)
    for row_idx in range(2, ws.max_row + 1):
        ws.row_dimensions[row_idx].height = 22
        is_even = (row_idx % 2 == 0)

        for col_idx in range(1, ws.max_column + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            if is_even:
                cell.fill = row_fill_even

            # จัด Format ตัวเลขเงิน
            if col_idx == 5: # คอลัมน์ราคา
                cell.alignment = align_right
                cell.number_format = "#,##0.00"
            elif col_idx in [1, 2, 4, 6]:
                cell.alignment = align_center
            else:
                cell.alignment = align_left

    # ปรับความกว้างคอลัมน์อัตโนมัติ
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            length = sum(2 if ord(char) > 127 else 1 for char in val_str)
            max_len = max(max_len, length)
        ws.column_dimensions[col_letter].width = max(max_len + 5, 12)

    # 5. บันทึกไฟล์
    filepath = "temp_sales_report.xlsx"
    wb.save(filepath)
    return filepath