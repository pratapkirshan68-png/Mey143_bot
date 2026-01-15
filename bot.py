import os
import asyncio
import sqlite3
import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait

# --- CONFIGURATION (ENV VARIABLES) ---
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "your_hash")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "your_token")
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "your_tmdb_key")

STORAGE_CHANNEL = int(os.environ.get("STORAGE_CHANNEL", "-1003536285620"))
SEARCH_CHAT = int(os.environ.get("SEARCH_CHAT", "-1003556253573"))
FILES_CHANNEL = int(os.environ.get("FILES_CHANNEL", "-1003682112470"))
ADMIN_ID = int(os.environ.get("ADMIN_ID", "12345678")) # Apna ID dalein

ENABLE_SHORTLINK = os.environ.get("ENABLE_SHORTLINK", "false").lower() == "true"
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "") # api.shareus.io etc
SHORTLINK_API = os.environ.get("SHORTLINK_API", "")

# --- DATABASE SETUP ---
db = sqlite3.connect("movies.db", check_same_thread=False)
cursor = db.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS movies 
               (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name TEXT, 
                file_id TEXT, 
                storage_msg_id INTEGER)''')
db.commit()

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- TMDB FUNCTION ---
def get_tmdb_data(query):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
        res = requests.get(url).json()
        if res['results']:
            movie = res['results'][0]
            return {
                "title": movie['title'],
                "year": movie['release_date'][:4] if movie.get('release_date') else "N/A",
                "poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}",
                "overview": movie['overview']
            }
    except:
        return None

# --- STEP 1: AUTO ADD FROM STORAGE ---
@bot.on_message(filters.chat(STORAGE_CHANNEL) & (filters.video | filters.document))
async def auto_add_to_db(client, message):
    movie_name = message.caption or "Unknown Movie"
    file_id = (message.video.file_id if message.video else message.document.file_id)
    
    cursor.execute("INSERT INTO movies (name, file_id, storage_msg_id) VALUES (?, ?, ?)", 
                   (movie_name, file_id, message.id))
    db.commit()
    print(f"Added to DB: {movie_name}")

# --- STEP 2 & 3: SEARCH LOGIC ---
@bot.on_message(filters.chat(SEARCH_CHAT) & filters.text)
async def search_movie(client, message):
    query = message.text
    cursor.execute("SELECT name, storage_msg_id FROM movies WHERE name LIKE ?", (f'%{query}%',))
    results = cursor.fetchall()

    if not results:
        no_found = await message.reply_text("❌ Movie nahi mili! Admin ko notify kar diya gaya hai.")
        await asyncio.sleep(60)
        await no_found.delete()
        return

    # User ko options dena (Agar multiple movies milein)
    for movie_name, msg_id in results[:3]: # Top 3 results
        tmdb = get_tmdb_data(movie_name)
        caption = f"🎬 **{movie_name}**\n\n📢 **Official Channel:** @YourChannel\n👑 **Uploaded by:** Pratap (Admin)\n\n━━━━━━━━━━━━━━"
        
        # Watermarked Send (COPY logic)
        try:
            if tmdb:
                await bot.send_photo(FILES_CHANNEL, photo=tmdb['poster'], caption=caption)
            
            await bot.copy_message(
                chat_id=FILES_CHANNEL,
                from_chat_id=STORAGE_CHANNEL,
                message_id=msg_id,
                caption=caption
            )
            
            success_msg = await message.reply_text(f"✅ Movie **{movie_name}** bhej di gayi hai: {FILES_CHANNEL}")
        except Exception as e:
            await message.reply_text(f"Error: {e}")

    # Auto Delete Search Query after 3 mins
    await asyncio.sleep(180)
    await message.delete()

# --- ADMIN COMMANDS ---
@bot.on_message(filters.command("pratap") & filters.user(ADMIN_ID))
async def stats(client, message):
    cursor.execute("SELECT COUNT(*) FROM movies")
    count = cursor.fetchone()[0]
    await message.reply_text(f"📊 **Total Movies in DB:** {count}")

@bot.on_message(filters.command("pratap2") & filters.user(ADMIN_ID))
async def delete_movie(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Example: `/pratap2 Pushpa 2` ")
    
    query = " ".join(message.command[1:])
    cursor.execute("DELETE FROM movies WHERE name LIKE ?", (f'%{query}%',))
    db.commit()
    await message.reply_text(f"🗑 Movie deleted from database related to: {query}")

print("Bot is running...")
bot.run()    
    if row:
        msg_id = row[0]
        try:
            await client.delete_messages(FILES_CHANNEL, msg_id)
            cursor.execute("DELETE FROM movies WHERE message_id = ?", (msg_id,))
            conn.commit()
            await message.reply("✅ Deleted from Channel and Database.")
        except Exception as e:
            # Fallback if channel delete fails but we still want to clean DB
            cursor.execute("DELETE FROM movies WHERE message_id = ?", (msg_id,))
            conn.commit()
            await message.reply(f"⚠️ Deleted from DB, but failed to delete from Channel: {e}")
    else:
        await message.reply("❌ Movie not found in DB.")
    conn.close()

# --- FILE INDEXER ---
@app.on_message(filters.chat(FILES_CHANNEL) & (filters.video | filters.document))
async def index_file(client, message):
    title = message.caption or "Unknown"
    add_movie(title, message.id, message.video.file_id if message.video else message.document.file_id)

# --- SEARCH LOGIC ---
@app.on_message(filters.chat(SEARCH_CHAT) & filters.text & ~filters.command(["pratap", "pratap2"]))
async def search_movie(client, message):
    query = message.text
    msg_id = get_movie(query)
    
    if not msg_id:
        return 

    tmdb_results = movie_search.search(query)
    caption = f"🎬 **Title:** {query.upper()}\n\n"
    
    if tmdb_results:
        movie = tmdb_results[0]
        caption += f"📝 **About:** {movie.overview[:200]}...\n"
        caption += f"⭐ **Rating:** {movie.vote_average}\n"

    caption += f"\n📢 **Join: @PratapCinema**"
    caption += get_invisible_watermark() 

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
    # Start the Flask web server in a separate thread
    threading.Thread(target=run_web, daemon=True).start()
    print("Bot is starting...")
    # Start the Telegram Bot
    app.run()
