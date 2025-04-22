import os
import psycopg2
from psycopg2.extras import DictCursor

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

def reset_database():
    """Drop all tables and recreate them with the new schema"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Drop existing tables if they exist
            print("Dropping existing tables...")
            cur.execute("""
                DROP TABLE IF EXISTS bookmark_tags CASCADE;
                DROP TABLE IF EXISTS summaries CASCADE;
                DROP TABLE IF EXISTS bookmarks CASCADE;
                DROP TABLE IF EXISTS tags CASCADE;
                DROP TABLE IF EXISTS collections CASCADE;
            """)
            
            # Create collections table
            print("Creating collections table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tags table
            print("Creating tags table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bookmarks table with title and collection_id
            print("Creating bookmarks table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    title TEXT,
                    collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create summaries table
            print("Creating summaries table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS summaries (
                    id SERIAL PRIMARY KEY,
                    bookmark_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,
                    summary TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bookmark_tags junction table
            print("Creating bookmark_tags junction table...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookmark_tags (
                    bookmark_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,
                    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (bookmark_id, tag_id)
                )
            """)
            
            # Create indexes for better performance
            print("Creating indexes...")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_collection_id ON bookmarks(collection_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_bookmark_tags_bookmark_id ON bookmark_tags(bookmark_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_bookmark_tags_tag_id ON bookmark_tags(tag_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_summaries_bookmark_id ON summaries(bookmark_id)")
            
        conn.commit()
        print("Database reset successful!")
    except psycopg2.Error as e:
        print(f"Error resetting database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    reset_database() 