import sqlite3
from datetime import datetime
from app.config import settings

def get_db_path():
    return settings.DATABASE_URL.replace("sqlite:///", "")

def init_db():
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id TEXT PRIMARY KEY,
            from_msisdn TEXT NOT NULL,
            to_msisdn TEXT NOT NULL,
            ts TEXT NOT NULL,
            text TEXT,
            created_at TEXT NOT NULL
        );
    """)
    conn.commit()
    conn.close()

def insert_message(data: dict) -> bool:
    """Returns True if inserted, False if duplicate (idempotent)"""
    conn = sqlite3.connect(get_db_path())
    cursor = conn.cursor()
    try:
        created_at = datetime.utcnow().isoformat() + "Z"
        cursor.execute("""
            INSERT INTO messages (message_id, from_msisdn, to_msisdn, ts, text, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (data['message_id'], data['from'], data['to'], data['ts'], data['text'], created_at))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_messages(limit: int, offset: int, from_filter: str = None, since_filter: str = None, search_q: str = None):
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = "SELECT * FROM messages WHERE 1=1"
    params = []
    
    if from_filter:
        query += " AND from_msisdn = ?"
        params.append(from_filter)
    if since_filter:
        query += " AND ts >= ?"
        params.append(since_filter)
    if search_q:
        query += " AND text LIKE ?"
        params.append(f"%{search_q}%")
        
    count_query = f"SELECT COUNT(*) as cnt FROM ({query})"
    cursor.execute(count_query, params)
    total = cursor.fetchone()['cnt']
    
    query += " ORDER BY ts ASC, message_id ASC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "message_id": row['message_id'],
            "from": row['from_msisdn'],
            "to": row['to_msisdn'],
            "ts": row['ts'],
            "text": row['text']
        })
        
    return results, total

def get_stats():
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    stats = {}
    
    cursor.execute("SELECT COUNT(*) as cnt FROM messages")
    stats['total_messages'] = cursor.fetchone()['cnt']
    
    cursor.execute("SELECT COUNT(DISTINCT from_msisdn) as cnt FROM messages")
    stats['senders_count'] = cursor.fetchone()['cnt']
    
    cursor.execute("""
        SELECT from_msisdn as 'from', COUNT(*) as count 
        FROM messages 
        GROUP BY from_msisdn 
        ORDER BY count DESC 
        LIMIT 10
    """)
    stats['messages_per_sender'] = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT MIN(ts) as first, MAX(ts) as last FROM messages")
    range_row = cursor.fetchone()
    stats['first_message_ts'] = range_row['first']
    stats['last_message_ts'] = range_row['last']
    
    conn.close()
    return stats