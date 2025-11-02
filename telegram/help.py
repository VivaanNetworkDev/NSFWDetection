from . import client
from pyrogram import filters

HELP_TEXT = (
    "I detect NSFW content in photos, stickers, GIFs and videos.\n\n"
    "- Send me a photo/sticker/GIF/video to check it.\n"
    "- In groups, make me admin with Delete Messages permission to auto-delete NSFW.\n\n"
    "Commands:\n"
    "/start - Introduction\n"
    "/help - How to use\n"
    "/ping - Check if I'm alive\n"
    "/stats - Usage stats"
)

@client.on_message(filters.command("help"))
async def help_cmd(_, message):
    await message.reply_text(HELP_TEXT)

# Friendly fallback in private chats for plain text
@client.on_message(filters.private & filters.text & ~filters.command(["start", "help", "ping", "stats"]))
async def help_private(_, message):
    await message.reply_text(HELP_TEXT)