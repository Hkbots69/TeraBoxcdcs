import telegram
import feedparser
import requests
from PIL import Image
from io import BytesIO
import os
import time

# Telegram bot API token
TOKEN = '6510025106:AAF8_zbcXcxCF0F5DbBkkOwG-hoiK4U2ovM'
# Channel name where bot will post updates
CHANNEL_NAME = '@epornerfeed'
# RSS Feed URL
RSS_FEED_URL = 'https://www.eporner.com/feed.rss'

# Initialize Telegram bot
bot = telegram.Bot(token=TOKEN)

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

# Main function to run the bot continuously
if __name__ == '__main__':
    while True:
        fetch_rss_and_send()
        time.sleep(60 * 60 * 24)  # Check for updates every 24 hours
