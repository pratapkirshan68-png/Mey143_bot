import os
import sqlite3
import threading
from flask import Flask
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tmdbv3api import TMDb, Movie
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SEARCH_CHAT = int(os.getenv("SEARCH_CHAT"))
FILES_CHANNEL = int(os.getenv("FILES_CHANNEL"))
TMDB_API_KEY = os.getenv("TMDB_API_KEY")
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS").split(",")]
WATERMARK_TEXT = os.getenv("WATERMARK_TEXT", "PratapCinema")

# TMDB Setup
tmdb = TMDb()
tmdb.api_key = TMDB_API_KEY
movie_search = Movie()

# Bot Setup
app = Client("movie_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Database Setup
def init_db():
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
                      (title TEXT, message_id INTEGER, file_id TEXT)''')
    conn.commit()
    conn.close()

def add_movie(title, msg_id, file_id):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO movies VALUES (?, ?, ?)", (title.lower(), msg_id, file_id))
    conn.commit()
    conn.close()

def get_movie(title):
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM movies WHERE title LIKE ?", ('%' + title.lower() + '%',))
    res = cursor.fetchone()
    conn.close()
    return res[0] if res else None

# --- INVISIBLE WATERMARK LOGIC ---
def get_invisible_watermark():
    # Uses Zero-Width Joiner/Non-Joiner to hide text
    mapping = {'0': '\u200B', '1': '\u200C', '2': '\u200D', '3': '\u2060'} 
    # Simply wrapping in hidden characters for this demo
    return f"\u200B\u200C{WATERMARK_TEXT}\u200D"

# --- ADMIN COMMANDS ---

@app.on_message(filters.command("pratap") & filters.user(ADMIN_IDS))
async def count_movies(client, message):
    conn = sqlite3.connect("movies.db")
    count = conn.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
    conn.close()
    await message.reply(f"📊 Total movies in DB: {count}")

@app.on_message(filters.command("pratap2") & filters.user(ADMIN_IDS))
async def delete_movie(client, message):
    if len(message.command) < 2:
        return await message.reply("Usage: /pratap2 movie name")
    
    query = " ".join(message.command[1:])
    conn = sqlite3.connect("movies.db")
    cursor = conn.cursor()
    cursor.execute("SELECT message_id FROM movies WHERE title LIKE ?", ('%' + query.lower() + '%',))
    row = cursor.fetchone()
    
    if row:
        msg_id = row[0]
        try:
            await client.delete_messages(FILES_CHANNEL, msg_id)
            cursor.execute("DELETE FROM movies WHERE message_id = ?", (msg_id,))
            conn.commit()
            await message.reply("✅ Deleted from Channel and Database.")
        except Exception as e:
            await message.reply(f"❌ Error deleting: {e}")
    else:
        await message.reply("❌ Movie not found in DB.")
    conn.close()

# --- FILE INDEXER ---
# When Admin sends a file to FILES_CHANNEL, it saves to DB
@app.on_message(filters.chat(FILES_CHANNEL) & (filters.video | filters.document))
async def index_file(client, message):
    title = message.caption or "Unknown"
    # Logic: If caption has a name, we use it as title
    add_movie(title, message.id, message.video.file_id if message.video else message.document.file_id)

# --- SEARCH LOGIC ---
@app.on_message(filters.chat(SEARCH_CHAT) & filters.text & ~filters.command(["pratap", "pratap2"]))
async def search_movie(client, message):
    query = message.text
    # 1. Search DB
    msg_id = get_movie(query)
    
    if not msg_id:
        return # Optionally reply "Not Found"

    # 2. Search TMDB for Poster/Details
    tmdb_results = movie_search.search(query)
    caption = f"🎬 **Title:** {query.upper()}\n\n"
    poster_url = None
    
    if tmdb_results:
        movie = tmdb_results[0]
        poster_url = f"https://image.tmdb.org/t/p/w500{movie.poster_path}"
        caption += f"📝 **About:** {movie.overview[:200]}...\n"
        caption += f"⭐ **Rating:** {movie.vote_average}\n"

    caption += f"\n📢 **Join: @PratapCinema**"
    caption += get_invisible_watermark() # Hidden Watermark

    # 3. RE-SEND FILE (No Forwarding)
    # copy_message creates a NEW message, removing "Forwarded From"
    await client.copy_message(
        chat_id=SEARCH_CHAT,
        from_chat_id=FILES_CHANNEL,
        message_id=msg_id,
        caption=caption,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Support Group", url="https://t.me/your_group")]
        ])
    )

# --- UPTIME ROBOT SERVER ---
web_app = Flask(__name__)
@web_app.route('/')
def home(): return "Bot is Alive"

def run_web():
    web_app.run(host="0.0.0.0", port=8080)

if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_web).start()
    print("Bot is starting...")
    app.run()        except Exception as e:
            await message.reply_text(f"✅ Deleted from DB, but failed to delete from Channel: {e}")
    else:
        await message.reply_text("❌ Movie not found.")

bot.run()
