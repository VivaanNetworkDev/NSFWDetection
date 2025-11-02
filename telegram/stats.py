from . import client
from pyrogram import filters
from .db import db

@client.on_message(filters.command("stats"))
async def stats(_, message):
    try:
        user_count = await db.users.count_documents({})
        chat_count = await db.chats.count_documents({})
        nsfw_count = await db.files.count_documents({"nsfw": True})
    except Exception:
        user_count = chat_count = nsfw_count = 0
    await message.reply_text(
        f"**Stats:**\n\nUsers: {user_count}\nChats: {chat_count}\nNSFW Files: {nsfw_count}"
    )
