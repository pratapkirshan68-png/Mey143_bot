import sqlite3

def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       title TEXT UNIQUE, 
                       message_id INTEGER, 
                       channel_id INTEGER)''')
    conn.commit()
    conn.close()

def add_movie(title, message_id, channel_id):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO movies (title, message_id, channel_id) VALUES (?, ?, ?)", 
                       (title.lower(), message_id, channel_id))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()

def search_movie_db(query):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT title, message_id FROM movies WHERE title LIKE ?", ('%' + query.lower() + '%',))
    res = cursor.fetchone()
    conn.close()
    return res

def delete_movie(title):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM movies WHERE title = ?", (title.lower(),))
    row = cursor.fetchone()
    if row:
        cursor.execute("DELETE FROM movies WHERE title = ?", (title.lower(),))
        conn.commit()
        conn.close()
        return row[0]
    conn.close()
    return None

def get_total_count():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    conn.close()
    return count
