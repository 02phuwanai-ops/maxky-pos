from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import OWNER_PIN


router = APIRouter()



@router.get(
    "/owner-login",
    response_class=HTMLResponse
)
def login_page():

    return """

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
content="width=device-width,initial-scale=1">


<style>

body{

font-family:Arial;

background:#f5f5f5;

text-align:center;

padding:40px;

}


input{

font-size:35px;

width:200px;

text-align:center;

border-radius:15px;

padding:10px;

}


button{

font-size:25px;

padding:15px 40px;

border-radius:20px;

margin-top:20px;

}

</style>

</head>


<body>


<h1>
👑 OWNER LOGIN
</h1>


<form method="post">


<input

type="password"

name="pin"

placeholder="PIN"


>


<br>


<button>

เข้าใช้งาน

</button>


</form>


</body>

</html>

"""




@router.post("/owner-login")
def login(pin:str = Form(...)):


    if pin == OWNER_PIN:


        response = RedirectResponse(
            "/owner",
            status_code=302
        )


        response.set_cookie(
            key="owner",
            value="yes",
            max_age=3600
        )


        return response



    return """

    <h2>

    ❌ PIN ไม่ถูกต้อง

    </h2>

    <a href="/owner-login">

    กลับ

    </a>

    """