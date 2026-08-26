from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routes.product import router as product_router
from app.routes.backup import router as backup_router
from app.routes.excel_export import router as excel_router
from app.routes.history import router as history_router
from app.routes.logout import router as logout_router
from app.routes.auth import router as auth_router
from app.routes.api_sale import router as api_sale_router
from app.routes.owner import router as owner_router
from app.routes.receive import router as receive_router
from app.routes.pdf_export import router as pdf_router
from app.routes.dashboard import router as dashboard_router
from app.routes.stock import router as stock_router
from app.routes.report import router as report_router
from app.routes.size import router as size_router
from app.routes.home import router as home_router
from app.routes.sale import router as sale_router
from app.routes.admin import router as admin_router
from app.routes.account import router as account_router

from app.database.receive_db import create_receive_table
from app.database.product_db import create_product_table
from app.database.db import DatabaseManager
from app.database.sales_db import create_sales_table
from app.database.stock_db import (
    create_stock_table,
    cleanup_orphan_stock
)
from app.database.account_db import init_account_db

# ==========================================
# FastAPI
# ==========================================

app = FastAPI(
    title="MAXKY POS",
    version="0.4"
)

@app.get("/ping")
def ping():
    return {"status": "alive"}

# ==========================================
# Templates
# ==========================================

templates = Jinja2Templates(
    directory="app/templates"
)

# ==========================================
# Static
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory="app/static"),
    name="static"
)

# ==========================================
# Routers
# ==========================================

app.include_router(home_router)
app.include_router(sale_router)
app.include_router(admin_router)
app.include_router(size_router)
app.include_router(report_router)
app.include_router(stock_router)
app.include_router(dashboard_router)
app.include_router(pdf_router)
app.include_router(receive_router)
app.include_router(owner_router)
app.include_router(api_sale_router)
app.include_router(auth_router)
app.include_router(logout_router)
app.include_router(history_router)
app.include_router(excel_router)
app.include_router(backup_router)
app.include_router(product_router)
app.include_router(account_router)

# ==========================================
# Database Startup
# ==========================================

@app.on_event("startup")
def startup():

    DatabaseManager.initialize()

    create_sales_table()
    create_stock_table()
    create_product_table()
    create_receive_table()
    init_account_db()

    cleanup_orphan_stock()

# ==========================================
# DEBUG ROUTES
# ==========================================

@app.get("/debug-routes")
def debug_routes():

    return [
        {
            "path": route.path,
            "name": route.name,
            "methods": list(route.methods or [])
        }
        for route in app.routes
        if hasattr(route, "methods")
    ]

# ==========================================
# DEBUG ROUTER DETAILS
# ==========================================

@app.get("/debug-routers")
def debug_routers():

    routers = {
        "home": home_router,
        "sale": sale_router,
        "admin": admin_router,
        "size": size_router,
        "report": report_router,
        "stock": stock_router,
        "dashboard": dashboard_router,
        "pdf": pdf_router,
        "receive": receive_router,
        "owner": owner_router,
        "api_sale": api_sale_router,
        "auth": auth_router,
        "logout": logout_router,
        "history": history_router,
        "excel": excel_router,
        "backup": backup_router,
        "product": product_router,
        "account": account_router,
    }

    result = {}

    for name, router in routers.items():

        result[name] = [
            {
                "path": route.path,
                "name": route.name,
                "methods": list(route.methods or [])
            }
            for route in router.routes
            if hasattr(route, "methods")
        ]

    return result