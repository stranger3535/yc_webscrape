import os
from dotenv import load_dotenv
import psycopg2

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def main():
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM companies;")
        count = cur.fetchone()[0]
        print("Connected to DB. companies count:", count)
        cur.close()
        conn.close()
    except Exception as e:
        print("DB connection error:", e)

if __name__ == "__main__":
    main()
