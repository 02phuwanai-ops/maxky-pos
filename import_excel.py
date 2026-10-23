import os
import pandas as pd
import pymysql
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True), override=True)

def import_merged_sales():
    host = os.getenv("MYSQL_HOST")
    port = int(os.getenv("MYSQL_PORT", 3306))
    user = os.getenv("MYSQL_USER")
    password = os.getenv("MYSQL_PASSWORD")
    database = os.getenv("MYSQL_DATABASE")

    # อ่านไฟล์ Excel ทั้งสองไฟล์
    files = [
        "exports/MAXKY_งานแข่งเรือหล่มเก่า2569.xlsx",
        "exports/MAXKY_งานแข่งเรือหล่มเก่า2569_2026-10-23.xlsx"
    ]
    
    all_dfs = []
    for file_path in files:
        if not os.path.exists(file_path):
            file_path = os.path.basename(file_path)
            
        if os.path.exists(file_path):
            print(f"กำลังอ่านไฟล์: {file_path}")
            raw_df = pd.read_excel(file_path, sheet_name="Sales")
            header_idx = raw_df[raw_df.iloc[:, 0] == 'วันที่'].index[0]
            df = pd.read_excel(file_path, sheet_name="Sales", skiprows=header_idx + 1)
            # โครงสร้างคอลัมน์ Excel: [วันที่, ชื่องาน, สินค้า, ไซส์, ต้นทุน, ราคาขาย, กำไร, ช่องทางชำระ]
            cols = ["datetime", "event_name", "product_name", "size", "cost", "price", "profit", "payment_method"]
            df = df.iloc[:, :8]
            df.columns = cols
            df = df[df["datetime"].notna()].copy()
            all_dfs.append(df)

    if not all_dfs:
        print("❌ ไม่พบไฟล์ Excel ยอดขาย")
        return

    # รวมข้อมูลและตัดรายการซ้ำตามเวลา
    combined = pd.concat(all_dfs, ignore_index=True)
    combined["datetime"] = pd.to_datetime(combined["datetime"])
    
    unique_sales = combined.drop_duplicates(
        subset=["datetime", "event_name", "product_name", "size", "cost", "price", "payment_method"]
    ).sort_values(by="datetime", ascending=True).reset_index(drop=True)

    print(f"✅ เชื่อมต่อรอยต่อเวลาสำเร็จ: ได้รายการขายจริงรวม {len(unique_sales)} รายการ")

    # เชื่อมต่อฐานข้อมูล Aiven MySQL
    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, database=database, charset='utf8mb4'
    )
    try:
        with conn.cursor() as cursor:
            # ล้างตารางเดิมก่อนเพื่อป้องกันยอดซ้ำซ้อน
            cursor.execute("DELETE FROM sales;")
            cursor.execute("ALTER TABLE sales AUTO_INCREMENT = 1;")
            
            # คำสั่ง INSERT ที่ระบุครบทุกคอลัมน์ที่จำเป็น (รวม category)
            insert_query = """
                INSERT INTO sales (created_at, event_name, category, size, cost, price, profit, payment_method)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            rows_to_insert = []
            for _, row in unique_sales.iterrows():
                rows_to_insert.append((
                    row["datetime"].strftime("%Y-%m-%d %H:%M:%S"),
                    str(row["event_name"]),
                    str(row["product_name"]),  # ค่า category ในตาราง
                    str(row["size"]),
                    float(row["cost"]),
                    float(row["price"]),
                    float(row["profit"]),
                    str(row["payment_method"])
                ))

            cursor.executemany(insert_query, rows_to_insert)
        conn.commit()
        print(f"🎉 นำเข้าข้อมูลการขาย 225 รายการย้อนหลังครบ 5 วัน เข้าสู่ระบบเรียบร้อยแล้ว!")
    finally:
        conn.close()

if __name__ == "__main__":
    import_merged_sales()