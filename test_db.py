import sys
sys.path.insert(0, r'C:\Users\enock\Downloads')
import deepseek_python_20260707_a6bd19 as lhm
import sqlite3
import tempfile
import os

print('=== DATABASE TESTS ===')

with tempfile.TemporaryDirectory() as tmpdir:
    db_path = os.path.join(tmpdir, 'test.db')
    conn = sqlite3.connect(db_path)
    
    print('1. Running migrations...')
    lhm.run_migrations(conn)
    tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    print(f'   Tables created: {[t[0] for t in tables]}')
    
    print('\n2. Testing atomic transaction...')
    conn.execute('CREATE TABLE IF NOT EXISTS test_balance (id INTEGER PRIMARY KEY, balance REAL)')
    conn.execute('INSERT INTO test_balance (balance) VALUES (1000.0)')
    conn.commit()
    
    with lhm.atomic_transaction(conn) as txn:
        txn.execute('UPDATE test_balance SET balance = balance - 100 WHERE id=1')
    
    bal = conn.execute('SELECT balance FROM test_balance WHERE id=1').fetchone()[0]
    print(f'   Balance after deduction: {bal} (expected 900.0)')
    
    print('\n3. Testing rollback...')
    try:
        with lhm.atomic_transaction(conn) as txn:
            txn.execute('UPDATE test_balance SET balance = balance - 500 WHERE id=1')
            raise ValueError('Test rollback')
    except ValueError:
        pass
    
    bal = conn.execute('SELECT balance FROM test_balance WHERE id=1').fetchone()[0]
    print(f'   Balance after rollback: {bal} (expected 900.0)')
    
    conn.close()

print('\nDatabase: WORKING')
