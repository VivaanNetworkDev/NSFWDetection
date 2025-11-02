import asyncio
import importlib
import logging
from pyrogram import idle
from telegram import client

# Import handlers to register them
importlib.import_module("telegram.antinsfw")
importlib.import_module("telegram.stats")
importlib.import_module("telegram.db")

async def gae():
    await client.start()
    await idle()
    await client.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Bot Started! Powered By @VivaanNetwork")
    # Install uvloop if available (Linux) but do not fail elsewhere
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass
    asyncio.run(gae())
