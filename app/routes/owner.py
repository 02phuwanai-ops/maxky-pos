from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from fastapi import Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")




router = APIRouter()


@router.get(
    "/owner",
    response_class=HTMLResponse
)
def owner(request:Request):


    if request.cookies.get("owner") != "yes":

        return RedirectResponse(
        "/owner-login"
    )

    return templates.TemplateResponse(
        request=request,
        name="owner.html",
        context={
            "request": request,
            "title": "OWNER PANEL"
        }
    )

