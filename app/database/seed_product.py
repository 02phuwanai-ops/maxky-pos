import sqlite3


DB_NAME = "data/maxky_pos.db"



products = [

("เสื้อยืด",60,100),

("เสื้อกีฬา",80,150),

("เสื้อยืดแขนยาว",100,180),

("เสื้อกีฬาแขนยาว",120,220),

("เสื้อฟอก",150,300),

("กางเกง",70,150)

]



conn = sqlite3.connect(DB_NAME)

cursor = conn.cursor()


cursor.executemany(

"""
INSERT OR IGNORE INTO products

(category,cost,price)

VALUES (?,?,?)

""",

products

)


conn.commit()

conn.close()


print("Product Cost Ready")