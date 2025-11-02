import os
import motor.motor_asyncio
from . import db_url

# Keep DB operations snappy if Mongo isn't available (avoid long hangs)
_timeout_ms = int(os.environ.get("DB_TIMEOUT_MS", "1500"))

try:
    client = motor.motor_asyncio.AsyncIOMotorClient(
        db_url,
        serverSelectionTimeoutMS=_timeout_ms,
        connectTimeoutMS=_timeout_ms,
        socketTimeoutMS=_timeout_ms,
    ) if db_url else None
except Exception:
    client = None

# Avoid truthiness checks on PyMongo/Motor objects; compare explicitly with None
db = client["nsfw"] if client is not None else None

userdb = db.users if db is not None else None
chatdb = db.chats if db is not None else None
files = db.files if db is not None else None
files_unique = db.files_unique if db is not None else None  # Separate collection keyed by Telegram file_unique_id

async def add_user(user_id: int, username: str):
    if userdb is None:
        return
    try:
        await userdb.update_one({"user_id": user_id}, {"$set": {"username": username}}, upsert=True)
    except Exception:
        # DB optional: ignore failures to keep bot responsive
        pass

async def add_chat(chat_id: int):
    if chatdb is None:
        return
    try:
        await chatdb.update_one({"chat_id": chat_id}, {"$set": {"chat_id": chat_id}}, upsert=True)
    except Exception:
        pass

async def is_nsfw(file_id: str):
    if files is None:
        return False
    try:
        m = await files.find_one({"file_id": file_id})
        if m:
            return m.get("nsfw", False)
    except Exception:
        pass
    return False

async def add_nsfw(file_id: str):
    if files is None:
        return
    try:
        await files.update_one({"file_id": file_id}, {"$set": {"nsfw": True}}, upsert=True)
    except Exception:
        pass

async def remove_nsfw(file_id: str):
    if files is None:
        return
    try:
        await files.update_one({"file_id": file_id}, {"$set": {"nsfw": False}}, upsert=True)
    except Exception:
        pass

# Unique-id based helpers to make repeated detections instant even if file_id changes
async def is_nsfw_unique(unique_id: str):
    if not unique_id:
        return False
    if files_unique is None:
        return False
    try:
        m = await files_unique.find_one({"unique_id": unique_id})
        if m:
            return m.get("nsfw", False)
    except Exception:
        pass
    return False

async def add_nsfw_unique(unique_id: str):
    if not unique_id:
        return
    if files_unique is None:
        return
    try:
        await files_unique.update_one({"unique_id": unique_id}, {"$set": {"nsfw": True}}, upsert=True)
    except Exception:
        pass

async def remove_nsfw_unique(unique_id: str):
    if not unique_id:
        return
    if files_unique is None:
        return
    try:
        await files_unique.update_one({"unique_id": unique_id}, {"$set": {"nsfw": False}}, upsert=True)
    except Exception:
        pass