from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/", response_class=HTMLResponse)
async def admin():

    return """
    <h1>Admin Page</h1>
    """