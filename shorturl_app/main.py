from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import sqlite3
import os
import hashlib

app = FastAPI(title="Short URL Service")

DB_PATH = "/app/data/shorturl.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            short_id TEXT PRIMARY KEY,
            full_url TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class URLCreate(BaseModel):
    url: str

def generate_short_id(url: str) -> str:
    return hashlib.md5(url.encode()).hexdigest()[:8]

@app.post("/shorten")
def shorten_url(url_data: URLCreate):
    short_id = generate_short_id(url_data.url)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT short_id FROM urls WHERE short_id = ?", (short_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO urls (short_id, full_url) VALUES (?, ?)", 
                      (short_id, url_data.url))
        conn.commit()
    
    conn.close()
    return {"short_id": short_id, "short_url": f"/{short_id}"}

@app.get("/{short_id}")
def redirect_url(short_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT full_url FROM urls WHERE short_id = ?", (short_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return RedirectResponse(url=row[0])

@app.get("/stats/{short_id}")
def get_stats(short_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT short_id, full_url FROM urls WHERE short_id = ?", (short_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Short URL not found")
    
    return {"short_id": row[0], "full_url": row[1]}