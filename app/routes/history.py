from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse


from app.database.history_db import get_sales_history



router = APIRouter()



@router.get(
    "/history",
    response_class=HTMLResponse
)
def history(request: Request):


    if request.cookies.get("owner") != "yes":

        return RedirectResponse(
            "/owner-login"
        )


    sales = get_sales_history()


    rows = ""


    for item in sales:


        date,category,size,price,profit=item


        rows += f"""

        <tr>

        <td>{date}</td>

        <td>{category}</td>

        <td>{size}</td>

        <td>{price}</td>

        <td>{profit}</td>


        </tr>

        """



    return f"""

<html>


<head>

<meta charset="UTF-8">


<meta name="viewport"
content="width=device-width,initial-scale=1">


<title>
Sales History
</title>


<style>

body{{

font-family:Arial;

background:#f5f5f5;

padding:20px;

}}


table{{

width:100%;

background:white;

border-collapse:collapse;

}}


td,th{{

padding:12px;

border-bottom:1px solid #ddd;

text-align:center;

}}


</style>


</head>



<body>


<h1>

📜 ประวัติการขาย

</h1>



<table>


<tr>

<th>
วันที่
</th>


<th>
สินค้า
</th>


<th>
ไซส์
</th>


<th>
ราคา
</th>


<th>
กำไร
</th>


</tr>



{rows}


</table>



</body>


</html>


"""