import sqlite3

# Connect to SQLite database (or create it)
conn = sqlite3.connect('freedom_wall.db')
cur = conn.cursor()

# Enable foreign key constraints (important for SQLite)
cur.execute('PRAGMA foreign_keys=off')

# Create or update `users` table
cur.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
)
''')

# --- Modify `posts` table to include `created_at`, index on `user_id`, and `ON DELETE CASCADE` constraint ---

# Step 1: Check if the `created_at` column exists; if not, add it.
try:
    cur.execute('ALTER TABLE posts ADD COLUMN created_at TIMESTAMP')
except sqlite3.OperationalError:
    # Column already exists
    pass

# Set default value for existing rows in `created_at` (if it's newly added)
cur.execute('UPDATE posts SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL')

# Step 2: Add index on `user_id` in `posts` table
cur.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON posts (user_id)')

# Step 3: Recreate the `posts` table with `ON DELETE CASCADE` for foreign key constraint
cur.execute('ALTER TABLE posts RENAME TO old_posts')

# Create the new `posts` table with the updated foreign key constraint
cur.execute('''
CREATE TABLE posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
)
''')

# Copy data from the old table to the new table
cur.execute('''
INSERT INTO posts (id, user_id, content, created_at)
SELECT id, user_id, content, created_at FROM old_posts
''')

# Drop the old table
cur.execute('DROP TABLE old_posts')

# Enable foreign key constraints again
cur.execute('PRAGMA foreign_keys=on')

# Commit the changes and close the connection
conn.commit()
conn.close()
