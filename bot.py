import requests
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import *
from database import init_db, add_movie, search_movie_db, delete_movie, get_total_count

bot = Client("MovieBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
init_db()

# --- TMDB HELPER ---
def get_tmdb_info(query):
    url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={query}"
    res = requests.get(url).json()
    if res.get("results"):
        movie = res["results"][0]
        return {
            "title": movie["original_title"],
            "poster": f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie['poster_path'] else None,
            "year": movie["release_date"][:4] if movie.get("release_date") else "N/A",
            "rating": movie["vote_average"]
        }
    return None

# --- AUTO-INDEXING (When Admin posts in FILES_CHANNEL) ---
@bot.on_message(filters.chat(FILES_CHANNEL) & (filters.video | filters.document))
async def index_handler(client, message):
    title = message.caption or (message.video.file_name if message.video else message.document.file_name)
    if title:
        add_movie(title, message.id, FILES_CHANNEL)

# --- USER SEARCH (Listens ONLY in SEARCH_CHAT) ---
@bot.on_message(filters.chat(SEARCH_CHAT) & filters.text & ~filters.command(["pratap", "pratap2"]))
async def search_handler(client, message):
    query = message.text
    db_movie = search_movie_db(query)
    
    if not db_movie:
        return # Skip if movie not in our channel

    # Fetch info from TMDB
    tmdb = get_tmdb_info(query)
    caption = f"🎬 **{db_movie[0].upper()}**\n\n"
    if tmdb:
        caption += f"🌟 Rating: {tmdb['rating']}\n📅 Year: {tmdb['year']}\n\n"
    
    caption += "✅ **Re-uploaded by Pratap Cinema**\n"
    caption += "🚫 Do not copy without permission.\n"
    caption += f"{INVISIBLE_WATERMARK}" # Anti-Theft Layer

    # Send Info Poster
    if tmdb and tmdb['poster']:
        await message.reply_photo(tmdb['poster'], caption=caption)

    # RE-SEND FILE (Anti-Theft: No Forward Tag)
    await client.copy_message(
        chat_id=message.chat.id,
        from_chat_id=FILES_CHANNEL,
        message_id=db_movie[1],
        caption=caption,
        reply_to_message_id=message.id
    )

# --- ADMIN COMMAND 1: /pratap ---
@bot.on_message(filters.command("pratap") & filters.user(ADMIN_IDS))
async def count_handler(client, message):
    count = get_total_count()
    await message.reply_text(f"🎬 **Total Movies in DB:** {count}")

# --- ADMIN COMMAND 2: /pratap2 ---
@bot.on_message(filters.command("pratap2") & filters.user(ADMIN_IDS))
async def delete_handler(client, message):
    if len(message.command) < 2:
        return await message.reply_text("Usage: `/pratap2 movie name`")
    
    movie_name = " ".join(message.command[1:])
    msg_id = delete_movie(movie_name)
    
    if msg_id:
        try:
            await client.delete_messages(FILES_CHANNEL, msg_id)
            await message.reply_text(f"✅ Deleted **{movie_name}** from DB and Channel.")
        except Exception as e:
            await message.reply_text(f"✅ Deleted from DB, but failed to delete from Channel: {e}")
    else:
        await message.reply_text("❌ Movie not found.")

bot.run()
