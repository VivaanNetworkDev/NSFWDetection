import os
import logging
from pyrogram import Client

# Read configuration from environment variables (Heroku/app.json compatible)
# These must be set in your environment for the bot to start.
api_id = int(os.environ.get("API_ID", "0"))
api_hash = os.environ.get("API_HASH", "")
bot_token = os.environ.get("BOT_TOKEN", "")
db_url = os.environ.get("MONGO_URI", "mongodb://localhost:27017")

if not bot_token or not api_id or not api_hash:
    logging.warning("Missing BOT_TOKEN/API_ID/API_HASH. Set env vars before starting the bot.")

client = Client("antinsfw", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

