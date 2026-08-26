import pymysql
from app.database.db import get_db_connection


def update_sales_table():
    conn = get_db_connection()
    try:
        columns = [
            ("cost", "DECIMAL(10,2) DEFAULT 0.00"),
            ("price", "DECIMAL(10,2) DEFAULT 0.00"),
            ("profit", "DECIMAL(10,2) DEFAULT 0.00"),
        ]

        with conn.cursor() as cursor:
            for name, datatype in columns:
                try:
                    cursor.execute(
                        f"""
                        ALTER TABLE sales
                        ADD COLUMN {name} {datatype}
                        """
                    )
                    conn.commit()
                except pymysql.Error:
                    # หากคอลัมน์มีอยู่แล้วใน MySQL จะข้ามโดยไม่ทำให้โปรแกรมพัง
                    pass
    finally:
        conn.close()


if __name__ == "__main__":
    update_sales_table()
    print("Sales table updated")