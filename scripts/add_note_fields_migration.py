"""Small migration script to add tags, event_date, event_time columns to notes table in PostgreSQL.

Usage: run this once after pulling changes:
    python scripts/add_note_fields_migration.py

It will check if columns exist and add them if missing.
"""
import os
import psycopg2
from psycopg2 import sql

# Load DATABASE_URL from environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment variables.")

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cursor = conn.cursor()
except psycopg2.OperationalError as e:
    print("Failed to connect to the database:", e)
    raise SystemExit(1)

# Define the columns to add
columns_to_add = {
    "tags": "TEXT",
    "event_date": "DATE",
    "event_time": "TIME"
}

# Check and add missing columns
try:
    for column, column_type in columns_to_add.items():
        cursor.execute(
            sql.SQL("""
                DO $$
                BEGIN
                    IF NOT EXISTS (
                        SELECT 1 FROM information_schema.columns
                        WHERE table_name = 'note' AND column_name = %s
                    ) THEN
                        ALTER TABLE note ADD COLUMN {} {};
                    END IF;
                END $$;
            """).format(sql.Identifier(column), sql.SQL(column_type)),
            [column]
        )
    print("Migration completed successfully.")
except psycopg2.Error as e:
    print("Error during migration:", e)
finally:
    cursor.close()
    conn.close()
