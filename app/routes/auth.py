from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import OWNER_PIN

router = APIRouter()


@router.get("/owner-login", response_class=HTMLResponse)
def login_page():
    return """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Owner Login - MAXKY POS</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Sarabun:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-main: #f8fafc;
            --text-main: #0f172a;
            --text-muted: #64748b;
            --primary-amber: #f59e0b;
            --primary-hover: #d97706;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Sarabun', 'Plus Jakarta Sans', sans-serif;
        }

        body {
            background-color: var(--bg-main);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .login-card {
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 24px;
            padding: 40px 32px;
            width: 100%;
            max-width: 400px;
            text-align: center;
            box-shadow: 0 10px 30px -5px rgba(0, 0, 0, 0.05);
            transition: all 0.3s ease;
        }

        .crown-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #fef3c7;
            color: #b45309;
            border: 1px solid #fde68a;
            padding: 6px 16px;
            border-radius: 50px;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 16px;
        }

        h1 {
            font-size: 26px;
            font-weight: 800;
            color: var(--text-main);
            margin-bottom: 6px;
            letter-spacing: -0.5px;
        }

        .subtitle {
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 32px;
            font-weight: 500;
        }

        .input-group {
            margin-bottom: 24px;
        }

        input[type="password"] {
            width: 100%;
            font-size: 28px;
            font-weight: 700;
            letter-spacing: 12px;
            text-align: center;
            padding: 14px 16px;
            border: 2px solid #e2e8f0;
            border-radius: 16px;
            outline: none;
            background: #f8fafc;
            color: var(--text-main);
            transition: all 0.2s ease;
        }

        input[type="password"]:focus {
            border-color: var(--primary-amber);
            background: #ffffff;
            box-shadow: 0 0 0 4px rgba(245, 158, 11, 0.15);
        }

        input[type="password"]::placeholder {
            letter-spacing: 2px;
            font-size: 16px;
            font-weight: 600;
            color: #cbd5e1;
        }

        button {
            width: 100%;
            background: var(--primary-amber);
            color: #ffffff;
            font-size: 16px;
            font-weight: 700;
            padding: 14px;
            border: none;
            border-radius: 16px;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(245, 158, 11, 0.25);
            transition: all 0.2s ease;
        }

        button:hover {
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(245, 158, 11, 0.35);
        }

        button:active {
            transform: translateY(0);
        }
    </style>
</head>
<body>

    <div class="login-card">
        <div class="crown-badge">👑 RESTRICTED AREA</div>
        <h1>OWNER LOGIN</h1>
        <div class="subtitle">กรอกรหัส PIN เพื่อเข้าสู่ระบบผู้ดูแล</div>

        <form method="post">
            <div class="input-group">
                <input 
                    type="password" 
                    name="pin" 
                    placeholder="ENTER PIN" 
                    maxlength="8"
                    autofocus 
                    required
                >
            </div>
            <button type="submit">
                เข้าใช้งานระบบ ➔
            </button>
        </form>
    </div>

</body>
</html>
"""


@router.post("/owner-login")
def login(pin: str = Form(...)):
    if pin == "30633063":
        response = RedirectResponse("/owner", status_code=302)
        response.set_cookie(key="owner", value="yes", max_age=3600)
        return response

    return """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - MAXKY POS</title>
    <link href="https://fonts.googleapis.com/css2?family=Sarabun:wght@500;700&display=swap" rel="stylesheet">
    <style>
        body {
            background-color: #f8fafc;
            font-family: 'Sarabun', sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            margin: 0;
        }
        .error-card {
            background: #ffffff;
            border: 1px solid #ffe4e6;
            border-radius: 20px;
            padding: 36px 28px;
            width: 100%;
            max-width: 360px;
            text-align: center;
            box-shadow: 0 10px 25px -5px rgba(225, 29, 72, 0.08);
        }
        .icon {
            font-size: 48px;
            margin-bottom: 12px;
        }
        h2 {
            font-size: 20px;
            color: #e11d48;
            margin-bottom: 8px;
            font-weight: 700;
        }
        p {
            font-size: 14px;
            color: #64748b;
            margin-bottom: 24px;
        }
        a {
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
        }
        a:hover {
            background: #e2e8f0;
            color: #0f172a;
        }
    </style>
</head>
<body>

    <div class="error-card">
        <div class="icon">🚫</div>
        <h2>รหัส PIN ไม่ถูกต้อง</h2>
        <p>กรุณาตรวจสอบรหัสผ่านอีกครั้ง</p>
        <a href="/owner-login">ลองใหม่อีกครั้ง</a>
    </div>

</body>
</html>
"""