import os

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


# ==========================================
# MAXKY POS
# Thai Font
# ==========================================

FONT_PATH = r"C:\Windows\Fonts\tahoma.ttf"
FONT_BOLD_PATH = r"C:\Windows\Fonts\tahomabd.ttf"


# ==========================================
# ตรวจสอบ Font
# ==========================================

if not os.path.exists(FONT_PATH):

    raise FileNotFoundError(
        "ไม่พบไฟล์ Tahoma.ttf ที่ C:\\Windows\\Fonts"
    )


if not os.path.exists(FONT_BOLD_PATH):

    raise FileNotFoundError(
        "ไม่พบไฟล์ Tahomabd.ttf ที่ C:\\Windows\\Fonts"
    )


# ==========================================
# Register Font
# ==========================================

pdfmetrics.registerFont(
    TTFont(
        "MAXKY_THAI",
        FONT_PATH
    )
)


pdfmetrics.registerFont(
    TTFont(
        "MAXKY_THAI_BOLD",
        FONT_BOLD_PATH
    )
)


# ==========================================
# สร้าง PDF
# ==========================================

def create_pdf(
    filename,
    data
):

    doc = SimpleDocTemplate(
        filename
    )


    styles = getSampleStyleSheet()


    # ======================================
    # Style
    # ======================================

    title_style = ParagraphStyle(

        "MAXKYTitle",

        parent=styles["Title"],

        fontName="MAXKY_THAI_BOLD",

        fontSize=20,

        leading=25,

        spaceAfter=20

    )


    heading_style = ParagraphStyle(

        "MAXKYHeading",

        parent=styles["Heading2"],

        fontName="MAXKY_THAI_BOLD",

        fontSize=14,

        leading=20,

        spaceAfter=10

    )


    normal_style = ParagraphStyle(

        "MAXKYNormal",

        parent=styles["Normal"],

        fontName="MAXKY_THAI",

        fontSize=11,

        leading=18

    )


    content = []


    # ==========================================
    # หัวรายงาน
    # ==========================================

    content.append(

        Paragraph(

            "MAXKY POS REPORT",

            title_style

        )

    )


    content.append(
        Spacer(1, 10)
    )


    # ==========================================
    # ชื่องาน
    # ==========================================

    event_name = data.get(
        "event_name",
        ""
    )


    if event_name:

        content.append(

            Paragraph(

                f"ชื่องาน : {event_name}",

                heading_style

            )

        )

    else:

        content.append(

            Paragraph(

                "ชื่องาน : ทุกงาน",

                heading_style

            )

        )


    content.append(
        Spacer(1, 15)
    )


    # ==========================================
    # สรุปยอด
    # ==========================================

    content.append(

        Paragraph(

            f"""
            จำนวนขาย : {data['qty']} ตัว
            <br/>
            ยอดขาย : {data['sales']:,.2f} บาท
            <br/>
            ต้นทุน : {data['cost']:,.2f} บาท
            <br/>
            กำไร : {data['profit']:,.2f} บาท
            """,

            normal_style

        )

    )


    content.append(
        Spacer(1, 20)
    )


    # ==========================================
    # รายการสินค้า
    # ==========================================

    content.append(

        Paragraph(

            "รายการสินค้า",

            heading_style

        )

    )


    for item in data["products"]:

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


        content.append(
            Spacer(1, 5)
        )


    # ==========================================
    # สร้าง PDF
    # ==========================================

    doc.build(
        content
    )