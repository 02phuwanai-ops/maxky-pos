from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import FileResponse

from app.utils.excel_export import create_excel


router = APIRouter()


# ==========================================
# Export Excel
# ==========================================

@router.get("/export/excel")
def export_excel(
    event_name: str = "",
    date: Optional[str] = Query(None, description="วันที่ต้องการ Export รูปแบบ YYYY-MM-DD")
):

    # --------------------------------------
    # รับชื่องาน และวันที่จาก URL
    # --------------------------------------

    event_name = event_name.strip()
    target_date = date.strip() if date else ""


    # --------------------------------------
    # สร้าง Excel
    # --------------------------------------
    try:
        filepath = create_excel(
            event_name=event_name,
            date=target_date
        )
    except TypeError:
        filepath = create_excel(
            event_name=event_name
        )


    # --------------------------------------
    # กำหนดชื่อไฟล์ส่งกลับ
    # --------------------------------------

    name_parts = []
    if event_name:
        safe_event = "".join(c for c in event_name if c not in '\\/:*?"<>|').strip()
        if safe_event:
            name_parts.append(safe_event)
    
    if target_date:
        name_parts.append(target_date)

    if name_parts:
        filename = f"MAXKY_{'_'.join(name_parts)}.xlsx"
    else:
        filename = "MAXKY_SALES.xlsx"


    return FileResponse(

        path=filepath,

        filename=filename,

        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )