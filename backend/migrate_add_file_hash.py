"""Migration script to add file_hash column to resumes table"""

import sys
import os
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings


def main():
    """Add file_hash column to resumes table"""
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite:///"):
        db_path = db_url.replace("sqlite:///", "")
    else:
        print("This script only works with SQLite databases")
        sys.exit(1)
    
    if not os.path.exists(db_path):
        print(f"Database not found: {db_path}")
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column already exists
    cursor.execute("PRAGMA table_info(resumes)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'file_hash' in columns:
        print("Column 'file_hash' already exists")
        conn.close()
        return
    
    # Add column
    cursor.execute("ALTER TABLE resumes ADD COLUMN file_hash TEXT")
    conn.commit()
    
    # Create unique index
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_resumes_file_hash ON resumes(file_hash)")
    conn.commit()
    
    print("Migration completed: file_hash column added")
    conn.close()


if __name__ == "__main__":
    main()

