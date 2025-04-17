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
            # Create collections table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS collections (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create tags table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS tags (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bookmarks table with title and collection_id
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id SERIAL PRIMARY KEY,
                    text TEXT NOT NULL,
                    title TEXT,
                    collection_id INTEGER REFERENCES collections(id) ON DELETE SET NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create bookmark_tags junction table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS bookmark_tags (
                    bookmark_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,
                    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (bookmark_id, tag_id)
                )
            """)
            
            # Create indexes for better performance
            cur.execute("CREATE INDEX IF NOT EXISTS idx_bookmarks_collection_id ON bookmarks(collection_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_bookmark_tags_bookmark_id ON bookmark_tags(bookmark_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_bookmark_tags_tag_id ON bookmark_tags(tag_id)")
            
        conn.commit()
    except psycopg2.Error as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def save_bookmark(text, title=None, collection_id=None, tag_ids=None):
    """Save a new text bookmark to the database with optional title, collection, and tags"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Insert the bookmark
            cur.execute(
                "INSERT INTO bookmarks (text, title, collection_id) VALUES (%s, %s, %s) RETURNING id",
                (text, title, collection_id)
            )
            bookmark_id = cur.fetchone()[0]
            
            # Add tags if provided
            if tag_ids:
                for tag_id in tag_ids:
                    cur.execute(
                        "INSERT INTO bookmark_tags (bookmark_id, tag_id) VALUES (%s, %s)",
                        (bookmark_id, tag_id)
                    )
                    
        conn.commit()
        return bookmark_id
    except psycopg2.Error as e:
        print(f"Error saving bookmark: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_bookmark(bookmark_id):
    """Retrieve a bookmark by ID with its collection and tags"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Get bookmark details
            cur.execute("""
                SELECT b.*, c.name as collection_name 
                FROM bookmarks b
                LEFT JOIN collections c ON b.collection_id = c.id
                WHERE b.id = %s
            """, (bookmark_id,))
            bookmark = cur.fetchone()
            
            if not bookmark:
                return None
                
            # Get tags for this bookmark
            cur.execute("""
                SELECT t.id, t.name
                FROM tags t
                JOIN bookmark_tags bt ON t.id = bt.tag_id
                WHERE bt.bookmark_id = %s
            """, (bookmark_id,))
            tags = cur.fetchall()
            
            result = dict(bookmark)
            result['tags'] = [dict(tag) for tag in tags]
            return result
    except psycopg2.Error as e:
        print(f"Error retrieving bookmark: {e}")
        raise
    finally:
        conn.close()

def get_all_bookmarks():
    """Retrieve all bookmarks with their collections and tags"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            # Get all bookmarks with collection names
            cur.execute("""
                SELECT b.*, c.name as collection_name 
                FROM bookmarks b
                LEFT JOIN collections c ON b.collection_id = c.id
                ORDER BY b.created_at DESC
            """)
            bookmarks = cur.fetchall()
            
            # Convert to list of dictionaries
            bookmarks_list = [dict(row) for row in bookmarks]
            
            # Get tags for all bookmarks
            bookmark_ids = [b['id'] for b in bookmarks_list]
            if bookmark_ids:
                cur.execute("""
                    SELECT bt.bookmark_id, t.id, t.name
                    FROM tags t
                    JOIN bookmark_tags bt ON t.id = bt.tag_id
                    WHERE bt.bookmark_id = ANY(%s)
                """, (bookmark_ids,))
                tags_by_bookmark = {}
                for row in cur.fetchall():
                    if row['bookmark_id'] not in tags_by_bookmark:
                        tags_by_bookmark[row['bookmark_id']] = []
                    tags_by_bookmark[row['bookmark_id']].append({
                        'id': row['id'],
                        'name': row['name']
                    })
                
                # Add tags to each bookmark
                for bookmark in bookmarks_list:
                    bookmark['tags'] = tags_by_bookmark.get(bookmark['id'], [])
            
            return bookmarks_list
    except psycopg2.Error as e:
        print(f"Error retrieving bookmarks: {e}")
        raise
    finally:
        conn.close()

def create_collection(name):
    """Create a new collection"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO collections (name) VALUES (%s) RETURNING id",
                (name,)
            )
            collection_id = cur.fetchone()[0]
        conn.commit()
        return collection_id
    except psycopg2.Error as e:
        print(f"Error creating collection: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_collections():
    """Get all collections"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM collections ORDER BY name")
            return [dict(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error retrieving collections: {e}")
        raise
    finally:
        conn.close()

def create_tag(name):
    """Create a new tag"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO tags (name) VALUES (%s) RETURNING id",
                (name,)
            )
            tag_id = cur.fetchone()[0]
        conn.commit()
        return tag_id
    except psycopg2.Error as e:
        print(f"Error creating tag: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_all_tags():
    """Get all tags"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("SELECT * FROM tags ORDER BY name")
            return [dict(row) for row in cur.fetchall()]
    except psycopg2.Error as e:
        print(f"Error retrieving tags: {e}")
        raise
    finally:
        conn.close()

def update_bookmark(bookmark_id, title=None, collection_id=None, tag_ids=None):
    """Update a bookmark's title, collection, and tags"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            # Update bookmark details
            update_fields = []
            params = []
            
            if title is not None:
                update_fields.append("title = %s")
                params.append(title)
                
            if collection_id is not None:
                update_fields.append("collection_id = %s")
                params.append(collection_id)
                
            if update_fields:
                params.append(bookmark_id)
                cur.execute(f"""
                    UPDATE bookmarks 
                    SET {', '.join(update_fields)}
                    WHERE id = %s
                """, params)
            
            # Update tags if provided
            if tag_ids is not None:
                # Remove existing tags
                cur.execute(
                    "DELETE FROM bookmark_tags WHERE bookmark_id = %s",
                    (bookmark_id,)
                )
                
                # Add new tags
                for tag_id in tag_ids:
                    cur.execute(
                        "INSERT INTO bookmark_tags (bookmark_id, tag_id) VALUES (%s, %s)",
                        (bookmark_id, tag_id)
                    )
                    
        conn.commit()
        return True
    except psycopg2.Error as e:
        print(f"Error updating bookmark: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def get_bookmarks_by_tag_id(tag_id):
    """Get all bookmarks that have a specific tag."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT b.id, b.text, b.title, b.collection_id, 
                           c.name as collection_name, b.created_at
                    FROM bookmarks b
                    LEFT JOIN collections c ON b.collection_id = c.id
                    JOIN bookmark_tags bt ON b.id = bt.bookmark_id
                    WHERE bt.tag_id = %s
                    ORDER BY b.created_at DESC
                """, (tag_id,))
                bookmarks = cur.fetchall()
                
                # Convert to list of dictionaries
                bookmarks_list = [dict(row) for row in bookmarks]
                
                # Get tags for all bookmarks
                bookmark_ids = [b['id'] for b in bookmarks_list]
                if bookmark_ids:
                    cur.execute("""
                        SELECT bt.bookmark_id, t.id, t.name
                        FROM tags t
                        JOIN bookmark_tags bt ON t.id = bt.tag_id
                        WHERE bt.bookmark_id = ANY(%s)
                    """, (bookmark_ids,))
                    tags_by_bookmark = {}
                    for row in cur.fetchall():
                        if row['bookmark_id'] not in tags_by_bookmark:
                            tags_by_bookmark[row['bookmark_id']] = []
                        tags_by_bookmark[row['bookmark_id']].append({
                            'id': row['id'],
                            'name': row['name']
                        })
                    
                    # Add tags to each bookmark
                    for bookmark in bookmarks_list:
                        bookmark['tags'] = tags_by_bookmark.get(bookmark['id'], [])
                
                return bookmarks_list
    except Exception as e:
        print(f"Error getting bookmarks by tag: {e}")
        raise

def get_bookmarks_by_collection_id(collection_id):
    """Get all bookmarks that belong to a specific collection."""
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=DictCursor) as cur:
                cur.execute("""
                    SELECT DISTINCT b.id, b.text, b.title, b.collection_id, 
                           c.name as collection_name, b.created_at
                    FROM bookmarks b
                    LEFT JOIN collections c ON b.collection_id = c.id
                    WHERE b.collection_id = %s
                    ORDER BY b.created_at DESC
                """, (collection_id,))
                bookmarks = cur.fetchall()
                
                # Convert to list of dictionaries
                bookmarks_list = [dict(row) for row in bookmarks]
                
                # Get tags for all bookmarks
                bookmark_ids = [b['id'] for b in bookmarks_list]
                if bookmark_ids:
                    cur.execute("""
                        SELECT bt.bookmark_id, t.id, t.name
                        FROM tags t
                        JOIN bookmark_tags bt ON t.id = bt.tag_id
                        WHERE bt.bookmark_id = ANY(%s)
                    """, (bookmark_ids,))
                    tags_by_bookmark = {}
                    for row in cur.fetchall():
                        if row['bookmark_id'] not in tags_by_bookmark:
                            tags_by_bookmark[row['bookmark_id']] = []
                        tags_by_bookmark[row['bookmark_id']].append({
                            'id': row['id'],
                            'name': row['name']
                        })
                    
                    # Add tags to each bookmark
                    for bookmark in bookmarks_list:
                        bookmark['tags'] = tags_by_bookmark.get(bookmark['id'], [])
                
                return bookmarks_list
    except Exception as e:
        print(f"Error getting bookmarks by collection: {e}")
        raise

# Initialize the database when the module is imported
if __name__ == "__main__":
    init_db()