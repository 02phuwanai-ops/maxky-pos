import os
import urllib.request
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from app.database.db import get_db_connection


# ==========================================
# MAXKY POS
# Thai Font Setup (Auto-download Sarabun)
# ==========================================

FONT_DIR = "/tmp/fonts"
FONT_PATH = os.path.join(FONT_DIR, "Sarabun-Regular.ttf")
FONT_BOLD_PATH = os.path.join(FONT_DIR, "Sarabun-Bold.ttf")

FONT_REGULAR_NAME = "Sarabun"
FONT_BOLD_NAME = "Sarabun-Bold"

def setup_thai_font():
    """โหลดและลงทะเบียนฟอนต์ภาษาไทยอัตโนมัติ"""
    try:
        os.makedirs(FONT_DIR, exist_ok=True)
        
        if not os.path.exists(FONT_PATH):
            url_regular = "https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Regular.ttf"
            urllib.request.urlretrieve(url_regular, FONT_PATH)
            
        if not os.path.exists(FONT_BOLD_PATH):
            url_bold = "https://github.com/google/fonts/raw/main/ofl/sarabun/Sarabun-Bold.ttf"
            urllib.request.urlretrieve(url_bold, FONT_BOLD_PATH)

        pdfmetrics.registerFont(TTFont(FONT_REGULAR_NAME, FONT_PATH))
        pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, FONT_BOLD_PATH))
        return True
    except Exception as e:
        print("Error registering Sarabun font:", e)
        return False

# เรียกใช้งานการตั้งค่าฟอนต์
setup_thai_font()


# ==========================================
# สร้าง PDF (รองรับ event_name และ date)
# ==========================================

def create_pdf(event_name="", date=""):

    os.makedirs(
        "reports",
        exist_ok=True
    )

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            event_name = event_name.strip()
            target_date = date.strip() if date else ""

            # ==========================================
            # สรุปยอดแยกตามช่องทางการชำระเงิน (ใช้ payment_method และ %% สำหรับ PyMySQL)
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

            # ==========================================
            # ดึงรายการสินค้า
            # ==========================================
            sql_products = """
                SELECT category, size, COUNT(*) as quantity
                FROM sales
                WHERE 1=1
            """
            params_products = []

            if event_name:
                sql_products += " AND TRIM(event_name) = TRIM(%s)"
                params_products.append(event_name)

            if target_date:
                sql_products += " AND DATE(created_at) = %s"
                params_products.append(target_date)

            sql_products += " GROUP BY category, size ORDER BY category, size"

            cursor.execute(sql_products, tuple(params_products))
            raw_products = cursor.fetchall()

            products = []
            for p in raw_products:
                if isinstance(p, dict):
                    products.append((
                        p.get("category", ""),
                        p.get("size", ""),
                        p.get("quantity", 0)
                    ))
                else:
                    products.append(p)

    finally:
        conn.close()

    # แปลงข้อมูลสรุปยอด
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

    # กำหนดชื่อไฟล์บันทึก
    name_parts = []
    if event_name:
        safe_name = "".join(c for c in event_name if c not in '\\/:*?"<>|').strip()
        if safe_name:
            name_parts.append(safe_name)
    if target_date:
        name_parts.append(target_date)

    if name_parts:
        filename = f"reports/MAXKY_{'_'.join(name_parts)}.pdf"
    else:
        filename = "reports/MAXKY_REPORT.pdf"

    # สร้างเอกสาร PDF
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "MAXKYTitle",
        parent=styles["Title"],
        fontName=FONT_BOLD_NAME,
        fontSize=20,
        leading=25,
        spaceAfter=15
    )

    heading_style = ParagraphStyle(
        "MAXKYHeading",
        parent=styles["Heading2"],
        fontName=FONT_BOLD_NAME,
        fontSize=13,
        leading=18,
        spaceAfter=8
    )

    normal_style = ParagraphStyle(
        "MAXKYNormal",
        parent=styles["Normal"],
        fontName=FONT_REGULAR_NAME,
        fontSize=11,
        leading=18
    )

    content = []

    # ==========================================
    # หัวรายงาน
    # ==========================================
    content.append(Paragraph("MAXKY POS REPORT", title_style))
    content.append(Spacer(1, 5))

    # ==========================================
    # ชื่องาน & วันที่
    # ==========================================
    if event_name:
        content.append(Paragraph(f"ชื่องาน : {event_name}", heading_style))
    else:
        content.append(Paragraph("ชื่องาน : ทุกงาน", heading_style))

    if target_date:
        content.append(Paragraph(f"วันที่ : {target_date}", heading_style))
    else:
        content.append(Paragraph("วันที่ : รวมทุกวัน (จบงาน)", heading_style))

    content.append(Spacer(1, 10))

    # ==========================================
    # สรุปยอด (รวมเงินสด, โอนเงิน, คนละครึ่ง)
    # ==========================================
    content.append(
        Paragraph(
            f"""
            จำนวนขาย : {qty:,.0f} ตัว
            <br/>
            ยอดขาย : {sales:,.2f} บาท
            <br/>
            ต้นทุน : {cost:,.2f} บาท
            <br/>
            กำไร : {profit:,.2f} บาท
            <br/>
            💵 เงินสด : {cash_total:,.2f} บาท
            <br/>
            📱 โอนเงิน : {transfer_total:,.2f} บาท
            <br/>
            🤝 คนละครึ่ง : {half_total:,.2f} บาท
            """,
            normal_style
        )
    )

    content.append(Spacer(1, 15))

    # ==========================================
    # รายการสินค้า
    # ==========================================
    content.append(Paragraph("รายการสินค้า", heading_style))

    if products:
        for item in products:
            category = item[0]
            size = item[1]
            quantity = item[2]

            content.append(
                Paragraph(
                    f"""
                    {category}
                    &nbsp;&nbsp;
                    ไซส์ {size}
                    &nbsp;&nbsp;
                    จำนวน {quantity} ตัว
                    """,
                    normal_style
                )
            )
            content.append(Spacer(1, 4))
    else:
        content.append(Paragraph("ไม่มีรายการขายในเงื่อนไขนี้", normal_style))

    doc.build(content)
    return filename