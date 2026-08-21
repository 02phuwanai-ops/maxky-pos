import sqlite3

DB = "data/maxky_pos.db"


def get_dashboard():
    # บังคับคืนค่า (ขายวันนี้, รายได้, กำไร) เป็น 0 ทั้งหมด
    return (0, 0, 0)


def get_stock_count():
    # บังคับคืนค่า สต๊อกทั้งหมด เป็น 0
    return 0


def get_low_stock_count():
    return 0


def get_low_stock_items():
    return []


def get_top_product():
    return "-"


def get_top_sales():
    return []