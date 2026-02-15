import sqlite3
import json
from typing import List, Dict, Optional
from datetime import datetime

DB_NAME = "transcriptions.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transcriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            transcript TEXT NOT NULL,
            audio_path TEXT,
            segments TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Simple migration: Adding columns if they don't exist
    cursor.execute("PRAGMA table_info(transcriptions)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'audio_path' not in columns:
        print("Migrating database: adding audio_path column")
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN audio_path TEXT")
    
    if 'segments' not in columns:
        print("Migrating database: adding segments column")
        cursor.execute("ALTER TABLE transcriptions ADD COLUMN segments TEXT")
        
    conn.commit()
    conn.close()

def add_transcription(filename: str, transcript: str, audio_path: str = None, segments: List = None) -> int:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    segments_json = json.dumps(segments) if segments else None
    cursor.execute(
        'INSERT INTO transcriptions (filename, transcript, audio_path, segments) VALUES (?, ?, ?, ?)', 
        (filename, transcript, audio_path, segments_json)
    )
    transcription_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return transcription_id

def get_transcriptions() -> List[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transcriptions ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    
    result = []
    for row in rows:
        item = dict(row)
        if item.get('segments'):
            item['segments'] = json.loads(item['segments'])
        result.append(item)
    return result

def get_transcription(id: int) -> Optional[Dict]:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transcriptions WHERE id = ?', (id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        item = dict(row)
        if item.get('segments'):
            item['segments'] = json.loads(item['segments'])
        return item
    return None

def delete_transcription(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transcriptions WHERE id = ?', (id,))
    conn.commit()
    conn.close()
