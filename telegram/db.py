import motor.motor_asyncio
from . import db_url

client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
db = client['nsfw']

userdb = db.users
chatdb = db.chats
files = db.files
files_unique = db.files_unique  # Separate collection keyed by Telegram file_unique_id

async def add_user(user_id: int, username: str):
    try:
        await userdb.update_one({'user_id': user_id}, {'$set': {'username': username}}, upsert=True)
    except Exception:
        # DB optional: ignore failures to keep bot responsive
        pass

async def add_chat(chat_id: int):
    try:
        await chatdb.update_one({'chat_id': chat_id}, {'$set': {'chat_id': chat_id}}, upsert=True)
    except Exception:
        pass

async def is_nsfw(file_id: str):
    try:
        m = await files.find_one({'file_id': file_id})
        if m:
            return m.get('nsfw', False)
    except Exception:
        pass
    return False

async def add_nsfw(file_id: str):
    try:
        await files.update_one({'file_id': file_id}, {'$set': {'nsfw': True}}, upsert=True)
    except Exception:
        pass

async def remove_nsfw(file_id: str):
    try:
        await files.update_one({'file_id': file_id}, {'$set': {'nsfw': False}}, upsert=True)
    except Exception:
        pass

# Unique-id based helpers to make repeated detections instant even if file_id changes
async def is_nsfw_unique(unique_id: str):
    if not unique_id:
        return False
    try:
        m = await files_unique.find_one({'unique_id': unique_id})
        if m:
            return m.get('nsfw', False)
    except Exception:
        pass
    return False

async def add_nsfw_unique(unique_id: str):
    if not unique_id:
        return
    try:
        await files_unique.update_one({'unique_id': unique_id}, {'$set': {'nsfw': True}}, upsert=True)
    except Exception:
        pass

async def remove_nsfw_unique(unique_id: str):
    if not unique_id:
        return
    try:
        await files_unique.update_one({'unique_id': unique_id}, {'$set': {'nsfw': False}}, upsert=True)
    except Exception:
        pass