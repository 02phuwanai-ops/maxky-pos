from fastapi import APIRouter
from fastapi.responses import RedirectResponse


router = APIRouter()



@router.get("/logout")
def logout():


    response = RedirectResponse(
        "/owner-login"
    )


    response.delete_cookie(
        "owner"
    )


    return response