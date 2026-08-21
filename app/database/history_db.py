import sqlite3


DB_NAME = "data/maxky_pos.db"



def get_sales_history():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        created_at,
        category,
        size,
        price,
        profit


        FROM sales


        ORDER BY id DESC


        LIMIT 50

        """
    )


    data = cursor.fetchall()


    conn.close()


    return data