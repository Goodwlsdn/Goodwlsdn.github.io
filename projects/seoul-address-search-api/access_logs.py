"""SQLite API access logs, with Seoul local timestamps."""
import json
import sqlite3
from datetime import datetime,timezone,timedelta

SEOUL=timezone(timedelta(hours=9))

def init_logs(db):
    c=sqlite3.connect(db,timeout=10)
    try:
        c.executescript('''CREATE TABLE IF NOT EXISTS api_logs(
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          request_id TEXT NOT NULL,
          requested_at TEXT NOT NULL,
          method TEXT NOT NULL,
          api_path TEXT NOT NULL,
          search_query TEXT,
          query_params TEXT NOT NULL,
          status_code INTEGER NOT NULL,
          success INTEGER NOT NULL CHECK(success IN(0,1)),
          duration_ms REAL NOT NULL,
          error_type TEXT);
          CREATE INDEX IF NOT EXISTS api_logs_time ON api_logs(requested_at);
          CREATE INDEX IF NOT EXISTS api_logs_path ON api_logs(api_path,id);
        ''')
        columns={r[1] for r in c.execute('PRAGMA table_info(api_logs)')}
        if 'result_count' not in columns:
            c.execute('ALTER TABLE api_logs ADD COLUMN result_count INTEGER CHECK(result_count>=0)')
        if 'result_status' not in columns:
            c.execute('ALTER TABLE api_logs ADD COLUMN result_status TEXT')
        c.commit()
    finally:c.close()

def write_log(db,entry):
    c=sqlite3.connect(db,timeout=5)
    try:
        c.execute('''INSERT INTO api_logs(request_id,requested_at,method,api_path,
          search_query,query_params,status_code,success,duration_ms,error_type,result_count,result_status)
          VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',entry)
        c.commit()
    finally:c.close()

def timestamp():
    return datetime.now(SEOUL).isoformat(timespec='milliseconds')
