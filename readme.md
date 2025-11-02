# NSFW Detection Telegram Bot

AI-powered moderation bot for Telegram that detects NSFW content in images, stickers, GIFs and videos using the Falconsai/nsfw_image_detection model.

Try it on Telegram: [@NsfwDetectorRobot](https://t.me/NsfwDetectorRobot)

## Features

- Detects NSFW content in:
  - Photos
  - Static stickers (webp)
  - Animated stickers (webm)
  - GIFs (downloaded as mp4)
  - Videos (samples frames for analysis)
- Works in groups (delete permission required) and private chats
- Fast re-detections via unique-id cache
- Persistent storage using MongoDB (via Motor)
- `/stats` command to view usage metrics

## Tech stack

- Python 3.11
- Pyrogram 2.x, tgcrypto/cryptg
- Transformers, Torch, OpenCV, Pillow
- Motor (MongoDB), uvloop

## Requirements

- Telegram Bot Token from [@BotFather](https://t.me/BotFather)
- API ID and API HASH from [my.telegram.org](https://my.telegram.org)
- MongoDB URI (MongoDB Atlas free tier recommended)

Environment variables expected by the bot:

- `BOT_TOKEN` — bot token from BotFather
- `API_ID` — numeric API ID
- `API_HASH` — API hash
- `MONGO_URI` — Mongo connection string (e.g. mongodb+srv://...)

## Quick start (local)

1) Clone and install dependencies
```bash
git clone https://github.com/VivaanNetworkDev/NSFWDetection
cd NSFWDetection
python3 -m pip install -U -r requirements.txt
```

2) Export environment variables
```bash
export BOT_TOKEN=your_bot_token
export API_ID=your_api_id
export API_HASH=your_api_hash
export MONGO_URI="your_mongodb_uri"
```

3) Run the bot
```bash
python3 -m telegram
```

## Usage

- Private chat: send any image/sticker/GIF/video and the bot will reply if it is NSFW.
- Groups: make the bot an admin with delete message permission; it will delete NSFW posts automatically and log the chat.

Available commands:
- `/start` — introduction and support links
- `/stats` — users, chats, and NSFW file count (from MongoDB)

## One‑click deploy to Heroku

This repository includes `Procfile`, `app.json`, and `runtime.txt` for Heroku.

- Deploy using the button below and fill in the required env vars:

[Deploy to Heroku](https://heroku.com/deploy?template=https://github.com/VivaanNetworkDev/NSFWDetection)

Heroku runs the worker: `python3 -m telegram` and uses Python `3.11.10` (see `runtime.txt`).

## CLI test (without Telegram)

You can run a simple CLI to check local files:

```bash
python3 main.py
```

It will prompt for an image or video path and print `NSFW` or `Not NSFW`.

## Acknowledgments

- Model: [`Falconsai/nsfw_image_detection`](https://huggingface.co/Falconsai/nsfw_image_detection)

## Support

If you find this project useful, consider supporting continued development.

Powered by VivaanNetwork — https://t.me/VivaanNetwork
