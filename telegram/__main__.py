import asyncio
import importlib
import logging
from pyrogram import idle
from pyrogram.types import BotCommand
from . import client

# Import handlers to register them (use package-relative to avoid name clashes)
importlib.import_module(".antinsfw", __package__)
importlib.import_module(".stats", __package__)
importlib.import_module(".db", __package__)
importlib.import_module(".ping", __package__)
importlib.import_module(".help", __package__)

async def gae():
    await client.start()
    me = await client.get_me()
    logging.info("Bot logged in as @%s (%s)", getattr(me, "username", None), me.id)
    try:
        await client.set_bot_commands([
            BotCommand("start", "Start the bot"),
            BotCommand("help", "How to use"),
            BotCommand("ping", "Check if bot is alive"),
            BotCommand("stats", "Usage stats"),
        ])
    except Exception:
        pass
    await idle()
    await client.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting bot... Powered By @VivaanNetwork")
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass
    asyncio.run(gae())
