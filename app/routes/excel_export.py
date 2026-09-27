from fastapi import APIRouter
from fastapi.responses import FileResponse

from app.utils.excel_export import create_excel


router = APIRouter()


# ==========================================
# Export Excel
# ==========================================

@router.get("/export/excel")
def export_excel(
    event_name: str = ""
):

    # --------------------------------------
    # รับชื่องานจาก URL
    # --------------------------------------

    event_name = event_name.strip()


    # --------------------------------------
    # สร้าง Excel
    # --------------------------------------

    filepath = create_excel(
        event_name
    )


    # --------------------------------------
    # ส่งไฟล์กลับ
    # --------------------------------------

    if event_name:

        safe_name = "".join(
            c for c in event_name
            if c not in '\\/:*?"<>|'
        ).strip()

        filename = (
            f"MAXKY_{safe_name}.xlsx"
        )

    else:

        filename = "MAXKY_SALES.xlsx"


    return FileResponse(

        path=filepath,

        filename=filename,

        media_type=
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    )
