from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import sqlite3
import os

app = FastAPI(title="TODO Service")

DB_PATH = "/app/data/todo.db"

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            completed BOOLEAN DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

class Item(BaseModel):
    title: str
    description: Optional[str] = None
    completed: bool = False

class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

@app.post("/items")
def create_item(item: Item):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO items (title, description, completed) VALUES (?, ?, ?)",
        (item.title, item.description, item.completed)
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"id": item_id, **item.dict()}

@app.get("/items")
def get_items():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM items")
    items = cursor.fetchall()
    conn.close()
    return [
        {"id": row[0], "title": row[1], "description": row[2], "completed": bool(row[3])}
        for row in items
    ]

@app.get("/items/{item_id}")
def get_item(item_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, description, completed FROM items WHERE id = ?", (item_id,))
    row = cursor.fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"id": row[0], "title": row[1], "description": row[2], "completed": bool(row[3])}

@app.put("/items/{item_id}")
def update_item(item_id: int, item: ItemUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM items WHERE id = ?", (item_id,))
    if cursor.fetchone() is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Item not found")
    
    updates = []
    values = []
    if item.title is not None:
        updates.append("title = ?")
        values.append(item.title)
    if item.description is not None:
        updates.append("description = ?")
        values.append(item.description)
    if item.completed is not None:
        updates.append("completed = ?")
        values.append(item.completed)
    
    if updates:
        values.append(item_id)
        cursor.execute(f"UPDATE items SET {', '.join(updates)} WHERE id = ?", values)
        conn.commit()
    
    conn.close()
    return {"message": "Item updated"}

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
    conn.commit()
    rows_deleted = cursor.rowcount
    conn.close()
    if rows_deleted == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"message": "Item deleted"}