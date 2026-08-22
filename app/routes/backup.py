from fastapi import APIRouter
from fastapi.responses import HTMLResponse, FileResponse
from pathlib import Path

from app.utils.backup_db import backup_database


router = APIRouter()


# ==========================================
# Backup Page
# ==========================================

@router.get(
    "/backup",
    response_class=HTMLResponse
)
def backup():

    filename = backup_database()
    backup_name = Path(filename).name

    return f"""
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Backup Successful - MAXKY POS</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-main: #f8fafc;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary-purple: #9333ea;
            --primary-hover: #7e22ce;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Sarabun', 'Plus Jakarta Sans', sans-serif;
        }}

        body {{
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .backup-card {{
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 40px 32px;
            width: 100%;
            max-width: 440px;
            text-align: center;
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05);
        }}

        .status-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #f3e8ff;
            color: #7e22ce;
            border: 1px solid #e9d5ff;
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 20px;
        }}

        .icon-box {{
            width: 64px;
            height: 64px;
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            border-radius: 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
            margin: 0 auto 16px;
        }}

        h2 {{
            font-size: 22px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 8px;
        }}

        .file-box {{
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 12px 16px;
            font-family: monospace;
            font-size: 13px;
            color: #475569;
            word-break: break-all;
            margin: 16px 0 28px;
        }}

        .btn-group {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}

        .btn {{
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            width: 100%;
            padding: 14px;
            font-size: 15px;
            font-weight: 700;
            border-radius: 14px;
            text-decoration: none;
            transition: all 0.2s ease;
            box-sizing: border-box;
            border: none;
            cursor: pointer;
        }}

        .btn-primary {{
            background: var(--primary-purple);
            color: #ffffff;
            box-shadow: 0 4px 12px rgba(147, 51, 234, 0.25);
        }}

        .btn-primary:hover {{
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(147, 51, 234, 0.35);
        }}

        .btn-secondary {{
            background: #f1f5f9;
            color: #475569;
        }}

        .btn-secondary:hover {{
            background: #e2e8f0;
            color: #0f172a;
        }}
    </style>
</head>
<body>

    <div class="backup-card">
        <div class="status-badge">💾 SYSTEM BACKUP</div>
        <div class="icon-box">✅</div>
        <h2>สำรองข้อมูลสำเร็จ!</h2>
        
        <div class="file-box">
            📁 {backup_name}
        </div>

        <div class="btn-group">
            <a href="/backup/download/{backup_name}" class="btn btn-primary">
                📥 ดาวน์โหลดไฟล์ Backup
            </a>
            <a href="/owner" class="btn btn-secondary">
                🏠 กลับหน้า Owner Panel
            </a>
        </div>
    </div>

</body>
</html>
"""


# ==========================================
# Download Backup
# ==========================================

@router.get("/backup/download/{filename}")
def download_backup(filename: str):

    backup_dir = Path("backup").resolve()
    requested_file = (backup_dir / filename).resolve()

    def render_error(message: str, status_code: int):
        return HTMLResponse(
            content=f"""
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - MAXKY POS</title>
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body {{
            background-color: #f8fafc;
            font-family: 'Sarabun', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            margin: 0;
        }}
        .error-card {{
            background: #ffffff;
            border: 1px solid #ffe4e6;
            border-radius: 20px;
            padding: 36px 28px;
            width: 100%;
            max-width: 380px;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(225, 29, 72, 0.08);
        }}
        .icon {{ font-size: 48px; margin-bottom: 12px; }}
        h2 {{ font-size: 20px; color: #e11d48; margin-bottom: 8px; font-weight: 700; }}
        p {{ font-size: 14px; color: #64748b; margin-bottom: 24px; }}
        a {{
            display: inline-block;
            width: 100%;
            padding: 12px;
            background: #f1f5f9;
            color: #334155;
            text-decoration: none;
            font-weight: 700;
            border-radius: 12px;
            transition: all 0.2s ease;
            box-sizing: border-box;
        }}
        a:hover {{ background: #e2e8f0; color: #0f172a; }}
    </style>
</head>
<body>
    <div class="error-card">
        <div class="icon">⚠️</div>
        <h2>เกิดข้อผิดพลาดในการดาวน์โหลด</h2>
        <p>{message}</p>
        <a href="/owner">กลับหน้า Owner Panel</a>
    </div>
</body>
</html>
""",
            status_code=status_code
        )

    # --------------------------------------
    # ป้องกันออกนอกโฟลเดอร์ backup
    # --------------------------------------

    if requested_file.parent != backup_dir:
        return render_error("ไม่อนุญาตให้เข้าถึงไฟล์นี้นอกโฟลเดอร์ Backup", 403)

    # --------------------------------------
    # ตรวจว่าไฟล์มีอยู่จริง
    # --------------------------------------

    if not requested_file.is_file():
        return render_error("ไม่พบไฟล์ Backup ที่ต้องการดาวน์โหลด", 404)

    # --------------------------------------
    # ส่งไฟล์ให้ Browser ดาวน์โหลด
    # --------------------------------------

    return FileResponse(
        path=str(requested_file),
        filename=requested_file.name,
        media_type="application/octet-stream"
    )