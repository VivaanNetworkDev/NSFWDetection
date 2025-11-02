import asyncio
import importlib
import logging
from pyrogram import idle
from . import client

# Import handlers to register them (use package-relative to avoid name clashes)
importlib.import_module(".antinsfw", __package__)
importlib.import_module(".stats", __package__)
importlib.import_module(".db", __package__)

async def gae():
    await client.start()
    me = await client.get_me()
    logging.info("Bot logged in as @%s (%s)", getattr(me, "username", None), me.id)
    await idle()
    await client.stop()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Starting bot... Powered By @VivaanNetwork")
    # Install uvloop if available (Linux) but do not fail elsewhere
    try:
        import uvloop
        uvloop.install()
    except Exception:
        pass
    asyncio.run(gae())
