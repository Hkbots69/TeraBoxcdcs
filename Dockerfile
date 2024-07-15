FROM hrishi2861/terabox:latest
WORKDIR /app

# Install required Python packages
RUN pip install python-telegram-bot \
                feedparser \
                Pillow \
                requests

# Copy all files from the current directory to /app in the container
COPY . .
CMD ["bash", "start.sh"]
