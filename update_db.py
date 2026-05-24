# -*- coding: utf-8 -*-
from app.main import get_db

def update_area():
    conn = get_db()
    conn.execute("UPDATE questions SET area = 'Matemáticas' WHERE area = 'Área General'")
    conn.commit()
    conn.close()
    print("DB Updated!")

if __name__ == "__main__":
    update_area()
