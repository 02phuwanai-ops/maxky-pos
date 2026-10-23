import pandas as pd
import pymysql
import os
from dotenv import load_dotenv, find_dotenv

# โหลดค่าเชื่อมต่อจาก .env
load_dotenv(find_dotenv(usecwd=True), override=True)

DB_HOST = os.getenv("MYSQL_HOST", "localhost")
DB_PORT = int(os.getenv("MYSQL_PORT", "3306"))
DB_USER = os.getenv("MYSQL_USER", "root")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
DB_NAME = os.getenv("MYSQL_DATABASE", "maxky_pos")

# ระบุตำแหน่งไฟล์ Excel (ปรับ path ตามจริง เช่น exports/MAXKY_SALES.xlsx หรือวางไว้ที่หลัก)
file_path = "MAXKY_SALES.xlsx"
if not os.path.exists(file_path):
    file_path = "exports/MAXKY_SALES.xlsx"

# ข้าม 10 แถวแรกที่เป็นส่วนสรุปหัวข้อ แล้วเริ่มอ่านตารางจริงตั้งแต่แถวที่ 11 เป็นต้นไป
df = pd.read_excel(file_path, sheet_name="Sales", skiprows=10, header=None)

# เชื่อมต่อ MySQL
conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    charset="utf8mb4"
)

try:
    with conn.cursor() as cursor:
        count = 0
        for index, row in df.iterrows():
            date_val = str(row.iloc[0]).strip()
            
            # กรองข้ามแถวว่าง หรือแถวหัวตารางซ้ำ
            if not date_val or date_val.lower() == "nan" or "วันที่" in date_val:
                continue

            try:
                created_at = date_val
                event_name = str(row.iloc[1]) if len(row) > 1 and pd.notna(row.iloc[1]) else "งานทั่วไป"
                category = str(row.iloc[2]) if len(row) > 2 and pd.notna(row.iloc[2]) else "สินค้า"
                size = str(row.iloc[3]) if len(row) > 3 and pd.notna(row.iloc[3]) else "F"
                
                cost_val = row.iloc[4] if len(row) > 4 else 0
                price_val = row.iloc[5] if len(row) > 5 else 0
                profit_val = row.iloc[6] if len(row) > 6 else 0
                payment_method = str(row.iloc[7]) if len(row) > 7 and pd.notna(row.iloc[7]) else "เงินสด"

                cost = float(cost_val) if pd.notna(cost_val) else 0.0
                price = float(price_val) if pd.notna(price_val) else 0.0
                profit = float(profit_val) if pd.notna(profit_val) else (price - cost)

            except Exception as ex:
                print(f"⚠️ ข้ามแถวที่ {index} เนื่องจากข้อมูลไม่สมบูรณ์: {ex}")
                continue

            sql = """
                INSERT INTO sales (category, size, created_at, cost, price, profit, event_name, payment_method, station_name, is_closed)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                category,
                size,
                created_at,
                cost,
                price,
                profit,
                event_name,
                payment_method,
                "จุดขายที่ 1",
                1  # ตั้งเป็น 1 เพื่อเก็บเป็นประวัติงานเก่า
            ))
            count += 1

        conn.commit()
        print(f"✅ นำเข้าข้อมูลจาก MAXKY_SALES.xlsx สำเร็จทั้งหมด {count} รายการเรียบร้อยแล้ว!")
finally:
    conn.close()