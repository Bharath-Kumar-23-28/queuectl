"""
Helper script to show database state during demos
Usage: python show_db.py [tables|schema|jobs|config|pending|all]
"""
import sqlite3
import sys
import time

def show_tables():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print('Tables:', ', '.join(tables))
    conn.close()

def show_schema():
    conn = sqlite3.connect('queuectl.db')
    print('\nJobs table structure:')
    cursor = conn.execute('PRAGMA table_info(jobs)')
    for row in cursor.fetchall():
        print(f'  {row[1]:15s} {row[2]}')
    
    print('\nConfig table structure:')
    cursor = conn.execute('PRAGMA table_info(config)')
    for row in cursor.fetchall():
        print(f'  {row[1]:15s} {row[2]}')
    conn.close()

def show_jobs():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute('SELECT id, state, attempts, max_retries FROM jobs ORDER BY created_at')
    print('\nJobs:')
    for row in cursor.fetchall():
        print(f'  {row[0]:25s} | {row[1]:12s} | attempts: {row[2]}/{row[3]}')
    conn.close()

def show_jobs_detailed():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute('SELECT id, state, attempts, max_retries, locked_by FROM jobs ORDER BY state, created_at')
    print('\nJobs (detailed):')
    for row in cursor.fetchall():
        worker = (row[4] or 'none')[:30] if row[4] else 'none'
        print(f'  {row[0]:25s} | {row[1]:12s} | {row[2]}/{row[3]} | worker: {worker}')
    conn.close()

def show_config():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute('SELECT key, value FROM config ORDER BY key')
    print('\nConfiguration:')
    for row in cursor.fetchall():
        print(f'  {row[0]:20s} = {row[1]}')
    conn.close()

def show_pending():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute('SELECT id, attempts, run_after FROM jobs WHERE state="pending" ORDER BY created_at')
    now = int(time.time())
    print('\nPending jobs:')
    for row in cursor.fetchall():
        ready_in = max(0, row[2] - now)
        status = f'ready in {ready_in}s' if ready_in > 0 else 'ready now'
        print(f'  {row[0]:25s} | attempts: {row[1]} | {status}')
    conn.close()

def show_dlq():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute('SELECT id, attempts, last_error FROM jobs WHERE state="dead"')
    print('\nDead Letter Queue:')
    for row in cursor.fetchall():
        error = (row[2] or '')[:60]
        print(f'  {row[0]:25s} | attempts: {row[1]}')
        if error:
            print(f'    Error: {error}')
    conn.close()

def show_stats():
    conn = sqlite3.connect('queuectl.db')
    cursor = conn.execute('SELECT state, COUNT(*) FROM jobs GROUP BY state')
    print('\nJob counts by state:')
    for row in cursor.fetchall():
        print(f'  {row[0]:12s}: {row[1]}')
    conn.close()

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'all'
    
    try:
        if command == 'tables':
            show_tables()
        elif command == 'schema':
            show_schema()
        elif command == 'jobs':
            show_jobs()
        elif command == 'detailed':
            show_jobs_detailed()
        elif command == 'config':
            show_config()
        elif command == 'pending':
            show_pending()
        elif command == 'dlq':
            show_dlq()
        elif command == 'stats':
            show_stats()
        elif command == 'all':
            show_jobs()
            show_stats()
        else:
            print('Usage: python show_db.py [tables|schema|jobs|detailed|config|pending|dlq|stats|all]')
    except sqlite3.OperationalError as e:
        print(f'Database error: {e}')
        print('Make sure queuectl.db exists')

if __name__ == '__main__':
    main()
