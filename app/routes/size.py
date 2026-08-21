from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)


sizes = [
    "S",
    "M",
    "L",
    "XL",
    "2XL",
    "3XL"
]


@router.get(
    "/size/{category}",
    response_class=HTMLResponse
)
async def size_page(
    request: Request,
    category: str
):

    return templates.TemplateResponse(
        request=request,
        name="size.html",
        context={
            "category": category,
            "sizes": sizes
        }
    )