import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB', 'scrollwise'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', ''),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432')
}

def get_db_connection():
    """Create and return a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to PostgreSQL: {e}")
        raise

def init_db():
    """Initialize the database and create necessary tables"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Create submissions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS submissions (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def save_submission(text):
    """Save a new text submission to the database"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO submissions (text) VALUES (%s) RETURNING id",
                (text,)
            )
            submission_id = cur.fetchone()[0]
        conn.commit()
        return submission_id
    except psycopg2.Error as e:
        print(f"Error saving submission: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_submission(submission_id):
    """Retrieve a submission by ID"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute(
                "SELECT * FROM submissions WHERE id = %s",
                (submission_id,)
            )
            result = cur.fetchone()
            return dict(result) if result else None
    except psycopg2.Error as e:
        print(f"Error retrieving submission: {e}")
        raise
    finally:
        conn.close()

def get_all_submissions():
    """Retrieve all submissions"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM submissions ORDER BY created_at DESC")
            results = cur.fetchall()
            return [dict(row) for row in results]
    except psycopg2.Error as e:
        print(f"Error retrieving submissions: {e}")
        raise
    finally:
        conn.close()

# Initialize the database when the module is imported
if __name__ == "__main__":
    init_db()