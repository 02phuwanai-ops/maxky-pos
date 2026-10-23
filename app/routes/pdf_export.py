from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.utils.pdf_report import create_pdf

router = APIRouter()

# ==========================================
# Export PDF
# ==========================================

@router.get("/export/pdf")
def export_pdf(
    event_name: str = "",
    date: Optional[str] = Query(None, description="วันที่ต้องการ Export รูปแบบ YYYY-MM-DD")
):
    event_name = event_name.strip()
    target_date = date.strip() if date else ""

    # เรียกใช้ฟังก์ชัน create_pdf จาก pdf_report.py
    try:
        filepath = create_pdf(
            event_name=event_name,
            date=target_date
        )
    except TypeError:
        # Fallback กรณีฟังก์ชันรับแค่ event_name แบบเดิม
        filepath = create_pdf(
            event_name=event_name
        )

    # กำหนดชื่อไฟล์ส่งกลับ
    name_parts = []
    if event_name:
        safe_event = "".join(c for c in event_name if c not in '\\/:*?"<>|').strip()
        if safe_event:
            name_parts.append(safe_event)
    
    if target_date:
        name_parts.append(target_date)

    if name_parts:
        filename = f"MAXKY_{'_'.join(name_parts)}.pdf"
    else:
        filename = "MAXKY_REPORT.pdf"

    return FileResponse(
        path=filepath,
        filename=filename,
        media_type="application/pdf"
    )