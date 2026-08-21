import sqlite3


DB_NAME = "data/maxky_pos.db"


def update_sales_table():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    columns = [
        ("cost","REAL"),
        ("price","REAL"),
        ("profit","REAL")
    ]


    for name,datatype in columns:

        try:

            cursor.execute(
                f"""
                ALTER TABLE sales
                ADD COLUMN {name} {datatype}
                """
            )

        except sqlite3.OperationalError:

            pass


    conn.commit()

    conn.close()


update_sales_table()

print("Sales table updated")