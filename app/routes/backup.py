from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

from app.utils.backup_db import backup_database


router = APIRouter()


# ==========================================
# Backup
# ==========================================

@router.get(
    "/backup",
    response_class=HTMLResponse
)
def backup():

    filename = backup_database()

    backup_name = Path(filename).name

    return f"""
    <html>
    <body style="font-family:Arial;text-align:center;padding:40px">

    <h2>✅ Backup สำเร็จ</h2>

    <p>{backup_name}</p>

    <br>

    <a href="/backup/download/{backup_name}">

        <button>
            💾 ดาวน์โหลด Backup
        </button>

    </a>

    <br><br>

    <a href="/owner">

        <button>
            กลับ Owner
        </button>

    </a>

    </body>
    </html>
    """


# ==========================================
# Download Backup
# ==========================================

@router.get("/backup/download/{filename}")
def download_backup(filename: str):

    backup_dir = Path("backup").resolve()

    requested_file = (
        backup_dir / filename
    ).resolve()

    # --------------------------------------
    # ป้องกันออกนอกโฟลเดอร์ backup
    # --------------------------------------

    if requested_file.parent != backup_dir:

        return HTMLResponse(
            content="❌ ไม่อนุญาตให้เข้าถึงไฟล์นี้",
            status_code=403
        )

    # --------------------------------------
    # ตรวจว่าไฟล์มีอยู่จริง
    # --------------------------------------

    if not requested_file.is_file():

        return HTMLResponse(
            content="❌ ไม่พบไฟล์ Backup",
            status_code=404
        )

    # --------------------------------------
    # ส่งไฟล์ให้ Browser ดาวน์โหลด
    # --------------------------------------

    return FileResponse(
        path=str(requested_file),
        filename=requested_file.name,
        media_type="application/octet-stream"
    )