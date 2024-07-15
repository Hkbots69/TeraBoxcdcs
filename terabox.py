import telegram
import feedparser
import requests
from PIL import Image
from io import BytesIO
import os
import time
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
import logging
import asyncio
from datetime import datetime
from pyrogram.enums import ChatMemberStatus
from dotenv import load_dotenv
from os import environ
from status import format_progress_bar
from video import download_video, upload_video
from web import keep_alive

# Load environment variables
load_dotenv('config.env', override=True)

# Telegram bot API token
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_API', '')
# Channel name where bot will post updates
CHANNEL_NAME = '@epornerfeed'
# RSS Feed URL
RSS_FEED_URL = 'https://www.eporner.com/feed.rss'

# Initialize Telegram bot
bot = telegram.Bot(token=TELEGRAM_TOKEN)

# Initialize Pyrogram client
api_id = os.environ.get('TELEGRAM_API', '')
api_hash = os.environ.get('TELEGRAM_HASH', '')
bot_token = os.environ.get('BOT_TOKEN', '')
dump_id = os.environ.get('DUMP_CHAT_ID', '')
if not all([api_id, api_hash, bot_token, dump_id]):
    logging.error("One or more environment variables are missing! Exiting now")
    exit(1)

app = Client("my_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Function to send message to Telegram channel
def send_message(title, description, video_link, image_url):
    # Format description with hashtags
    hashtags = ' '.join(f'#{tag.strip()}' for tag in description.split(','))
    message = f"*{title}*\n\n{hashtags}\n\n[Click for Video]({video_link})"
    
    # Download and send image
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            # Convert image to bytes
            image_bytes = BytesIO()
            image.save(image_bytes, format='JPEG')
            image_bytes.seek(0)
            # Send photo with caption
            bot.send_photo(chat_id=CHANNEL_NAME, photo=image_bytes, caption=message, parse_mode=telegram.ParseMode.MARKDOWN)
    except Exception as e:
        print(f"Failed to send message: {e}")

# Function to fetch and process RSS feed
def fetch_rss_and_send():
    feed = feedparser.parse(RSS_FEED_URL)
    sent_links = set()

    for entry in feed.entries:
        title = entry.title
        video_link = entry.link
        description = entry.description

        # Extract image URL from enclosure tag
        try:
            image_url = entry.enclosures[0]['url']
        except (IndexError, KeyError):
            continue
        
        # Check if already sent this link
        if video_link in sent_links:
            continue

        # Send message to Telegram
        send_message(title, description, video_link, image_url)
        sent_links.add(video_link)

# Pyrogram handlers
@app.on_message(filters.command("start"))
async def start_command(client, message):
    sticker_message = await message.reply_sticker("CAACAgIAAxkBAAEYonplzwrczhVu3I6HqPBzro3L2JU6YAACvAUAAj-VzAoTSKpoG9FPRjQE")
    await asyncio.sleep(2)
    await sticker_message.delete()
    user_mention = message.from_user.mention
    reply_message = f"ᴡᴇʟᴄᴏᴍᴇ, {user_mention}.\n\n🌟 ɪ ᴀᴍ ᴀ ᴛᴇʀᴀʙᴏx ᴅᴏᴡɴʟᴏᴀᴅᴇʀ ʙᴏᴛ. sᴇɴᴅ ᴍᴇ ᴀɴʏ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ ɪ ᴡɪʟʟ ᴅᴏᴡɴʟᴏᴀᴅ ᴡɪᴛʜɪɴ ғᴇᴡ sᴇᴄᴏɴᴅs ᴀɴᴅ sᴇɴᴅ ɪᴛ ᴛᴏ ʏᴏᴜ ✨."
    join_button = InlineKeyboardButton("ᴊᴏɪɴ ❤️🚀", url="https://t.me/ceabox")
    developer_button = InlineKeyboardButton("ᴅᴇᴠᴇʟᴏᴘᴇʀ ⚡️", url="https://t.me/ceabox")
    reply_markup = InlineKeyboardMarkup([[join_button, developer_button]])
    await message.reply_text(reply_message, reply_markup=reply_markup)

async def is_user_member(client, user_id):
    # Implement your membership status logic here if needed
    return True

@app.on_message(filters.text)
async def handle_message(client, message: Message):
    user_id = message.from_user.id
    user_mention = message.from_user.mention
    logging.info(f"Received message from {user_mention} (user_id: {user_id})")
    
    is_member = await is_user_member(client, user_id)

    if not is_member:
        logging.info(f"User {user_mention} (user_id: {user_id}) is not a member of the required channel")
        join_button = InlineKeyboardButton("Join ❤️🚀", url="https://t.me/ceabox")
        reply_markup = InlineKeyboardMarkup([[join_button]])
        await message.reply_text("You must join my channel to use me.", reply_markup=reply_markup)
        return

    terabox_link = message.text.strip()
    if "terabox" not in terabox_link:
        await message.reply_text("ᴘʟᴇᴀsᴇ sᴇɴᴅ ᴀ ᴠᴀʟɪᴅ ᴛᴇʀᴀʙᴏx ʟɪɴᴋ.")
        return

    reply_msg = await message.reply_text("sᴇɴᴅɪɴɢ ʏᴏᴜ ᴛʜᴇ ᴍᴇᴅɪᴀ...🤤")

    try:
        file_path, thumbnail_path, video_title = await download_video(terabox_link, reply_msg, user_mention, user_id)
        await upload_video(client, file_path, thumbnail_path, video_title, reply_msg, dump_id, user_mention, user_id, message)
    except Exception as e:
        logging.error(f"Error handling message: {e}")
        await reply_msg.edit_text("ғᴀɪʟᴇᴅ ᴛᴏ ᴘʀᴏᴄᴇss ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ.\nɪғ ʏᴏᴜʀ ғɪʟᴇ sɪᴢᴇ ɪs ᴍᴏʀᴇ ᴛʜᴀɴ 120ᴍʙ ɪᴛ ᴍɪɢʜᴛ ғᴀɪʟ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ.\nᴛʜɪs ɪs ᴛʜᴇ ᴛᴇʀᴀʙᴏx ɪssᴜᴇ, sᴏᴍᴇ ʟɪɴᴋs ᴀʀᴇ ʙ

if __name__ == "__main__":
    keep_alive()
    app.run()
