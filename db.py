import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return pymysql.connect(
        host = os.getenv('DB_HOST','localhost'),
        port= int(os.getenv('DB_PORT',3306)),
        user= os.getenv('DB_USER','root'),
        passwd= os.getenv('DB_PASSWORD','123456'),
        database= os.getenv('DB_NAME','rag_demo'),
        charset= 'utf8mb4',
        cursorclass=pymysql.cursors.DictCursor 
    )
    
def save_message(session_id,role,content,sources = None):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "INSERT INTO chat_history(session_id,role,content,sources) VALUES (%s,%s,%s,%s)"
            
            cursor.execute(sql,(session_id,role,content,sources))
        conn.commit()
    finally:
        conn.close()
        
def get_history(session_id,limit=20):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT role,content,sources,created_at FROM chat_history WHERE session_id=%s ORDER BY id DESC LIMIT %s"
            cursor.execute(sql,(session_id,limit))
            rows = cursor.fetchall()
        return list(reversed(rows))
    finally:
        conn.close()
        