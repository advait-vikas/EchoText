import sqlite3
import json
import os
from typing import List, Dict, Optional
from datetime import datetime

# Default name, can be overridden by calling set_db_path
_DB_PATH = "transcriptions.db"

def set_db_path(path: str):
    global _DB_PATH
    _DB_PATH = path

def get_connection():
    return sqlite3.connect(_DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            transcript TEXT NOT NULL,
            audio_path TEXT,
            segments TEXT,
            summary TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Simple migration: Adding columns if they don't exist
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'audio_path' not in columns:
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN audio_path TEXT")
    
    if 'segments' not in columns:
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN segments TEXT")
    
    if 'summary' not in columns:
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN summary TEXT")
        
    conn.commit()
    conn.close()

def add_transcription(filename: str, transcript: str, audio_path: str = None, segments: List = None, summary: str = None) -> int:
    conn = get_connection()
    cursor = conn.cursor()
    segments_json = json.dumps(segments) if segments else None
    cursor.execute(
        'INSERT INTO transcriptions (filename, transcript, audio_path, segments, summary) VALUES (?, ?, ?, ?, ?)', 
        (filename, transcript, audio_path, segments_json, summary)
    )
    transcription_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transcription_id

def get_transcriptions() -> List[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transcriptions ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        item = dict(row)
        if item.get('segments'):
            try:
                item['segments'] = json.loads(item['segments'])
            except:
                item['segments'] = []
        if item.get('summary'):
            try:
                item['summary'] = json.loads(item['summary'])
            except:
                pass
        result.append(item)
    return result

def get_transcription(id: int) -> Optional[Dict]:
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transcriptions WHERE id = ?', (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        if item.get('segments'):
            try:
                item['segments'] = json.loads(item['segments'])
            except:
                item['segments'] = []
        if item.get('summary'):
            try:
                item['summary'] = json.loads(item['summary'])
            except:
                pass
        return item
    return None

def update_summary(id: int, summary: dict):
    conn = get_connection()
    cursor = conn.cursor()
    summary_json = json.dumps(summary)
    cursor.execute('UPDATE transcriptions SET summary = ? WHERE id = ?', (summary_json, id))
    conn.commit()
    conn.close()

def delete_transcription(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transcriptions WHERE id = ?', (id,))
    conn.commit()
    conn.close()
