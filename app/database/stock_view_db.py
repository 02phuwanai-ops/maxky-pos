import sqlite3


DB_NAME = "data/maxky_pos.db"



def get_stock_all():


    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        category,
        size,
        quantity

        FROM stock

        ORDER BY category,size

        """
    )


    data = cursor.fetchall()


    conn.close()


    return data

def get_low_stock():

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()


    cursor.execute(
        """
        SELECT

        category,
        size,
        quantity

        FROM stock

        WHERE quantity <= 5

        ORDER BY quantity ASC

        """
    )


    data = cursor.fetchall()


    conn.close()


    return data