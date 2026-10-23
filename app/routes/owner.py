from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

# นำเข้าฟังก์ชันดึงรายชื่อชื่องานทั้งหมด
from app.database.sales_db import get_event_names

templates = Jinja2Templates(directory="app/templates")

router = APIRouter()


@router.get(
    "/owner",
    response_class=HTMLResponse
)
def owner(request: Request):

    if request.cookies.get("owner") != "yes":

        return RedirectResponse(
            "/owner-login"
        )

    # ดึงชื่องานทั้งหมดจากฐานข้อมูล
    event_names = get_event_names()

    return templates.TemplateResponse(
        request=request,
        name="owner.html",
        context={
            "request": request,
            "title": "OWNER PANEL",
            "event_names": event_names  # ส่งรายชื่อชื่องานไปแสดงในหน้า HTML
        }
    )