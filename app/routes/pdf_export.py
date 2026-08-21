from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.database.report_db import get_today_report
from app.utils.pdf_report import create_pdf


router = APIRouter()


@router.get("/export/pdf")
def export_pdf(
    event_name: str = ""
):

    # ==========================================
    # ชื่องาน
    # ==========================================

    event_name = event_name.strip()


    # ==========================================
    # ชื่อไฟล์ PDF
    # ==========================================

    if event_name:

        filename = "MAXKY_Report.pdf"

    else:

        filename = "MAXKY_Report.pdf"


    # ==========================================
    # ดึงข้อมูลรายงาน
    # ==========================================

    data = get_today_report(
        event_name
    )


    # ==========================================
    # สร้าง PDF
    # ==========================================

    create_pdf(
        filename,
        data
    )


    # ==========================================
    # ส่งไฟล์กลับ
    # ==========================================

    return FileResponse(

        filename,

        media_type="application/pdf",

        filename=filename

    )
