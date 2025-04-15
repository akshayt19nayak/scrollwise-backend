import psycopg2

# Database connection details
DB_NAME = "bookmarker"
DB_USER = "username"
DB_PASSWORD = "password"
DB_HOST = "localhost"
DB_PORT = "5432"

# SQL statements to create tables
CREATE_TABLES_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS bookmarks (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    url TEXT NOT NULL,
);

CREATE TABLE IF NOT EXISTS tags (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS bookmark_tags (
    bookmark_id INTEGER REFERENCES bookmarks(id) ON DELETE CASCADE,
    tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (bookmark_id, tag_id)
);
"""

# Connect to PostgreSQL and create tables
try:
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    cursor = conn.cursor()

    # Execute the SQL statements
    cursor.execute(CREATE_TABLES_SQL)
    
    # Commit changes
    conn.commit()
    print("Tables created successfully!")

except Exception as e:
    print("Error:", e)

finally:
    if cursor:
        cursor.close()
    if conn:
        conn.close()