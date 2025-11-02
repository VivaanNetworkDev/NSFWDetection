from . import client
from pyrogram import filters

@client.on_message(filters.command("ping"))
async def ping(_, message):
    await message.reply_text("pong")