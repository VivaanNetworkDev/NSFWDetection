import cv2
import os
import logging
import asyncio
import tempfile
from PIL import Image
import torch
from . import client
from pyrogram import filters
from .db import (
    is_nsfw,
    add_chat,
    add_user,
    add_nsfw,
    remove_nsfw,
    is_nsfw_unique,
    add_nsfw_unique,
    remove_nsfw_unique,
)
from .cache import (
    is_nsfw_cached,
    mark_nsfw_cached,
    mark_safe_cached,
)
from transformers import AutoModelForImageClassification, AutoImageProcessor
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Lazy, thread-safe model loading to keep /start responsive on cold boot
_model = None
_processor = None
_model_lock = asyncio.Lock()

async def get_model_and_processor():
    global _model, _processor
    if _model is not None and _processor is not None:
        return _model, _processor
    async with _model_lock:
        if _model is None or _processor is None:
            def _load():
                m = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
                p = AutoImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
                m.eval()
                return m, p
            _model, _processor = await asyncio.to_thread(_load)
    return _model, _processor

def _predict_is_nsfw_sync(image: Image.Image) -> bool:
    """Synchronous prediction; returns True if predicted label contains 'nsfw'."""
    model, processor = _model, _processor
    if model is None or processor is None:
        # Should not happen when called via classify_image_async, but be safe
        model, processor = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection"), AutoImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
        model.eval()
    with torch.no_grad():
        inputs = processor(images=image, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits
        idx = int(logits.argmax(-1).item())
        label = str(getattr(model.config, "id2label", {}).get(idx, "")).lower()
    # Fallback: if mapping missing, assume class 1 is nsfw as commonly used
    return ("nsfw" in label) or (label == "" and idx == 1)

async def classify_image_async(image: Image.Image) -> bool:
    """Run classification in a thread to avoid blocking the event loop."""
    # Ensure model is loaded (non-blocking to event loop)
    await get_model_and_processor()
    return await asyncio.to_thread(_predict_is_nsfw_sync, image)

def sample_video_frames(path: str, sample_seconds=(0, 6, 12), max_frames=3):
    """Efficiently sample a few frames from a video at given seconds."""
    cap = cv2.VideoCapture(path)
    frames = []
    try:
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0
        duration = (frame_count / fps) if fps and frame_count else None

        for s in sample_seconds:
            if duration is not None and s > duration:
                break
            cap.set(cv2.CAP_PROP_POS_MSEC, s * 1000)
            success, frame = cap.read()
            if not success or frame is None:
                continue
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frames.append(img)
            if len(frames) >= max_frames:
                break
    finally:
        cap.release()
    return frames

@client.on_message(filters.photo | filters.sticker | filters.animation | filters.video)
async def getimage(client, event):
    # Determine file_id and unique_id
    file_id = None
    unique_id = None
    if event.photo:
        file_id = event.photo.file_id
        unique_id = event.photo.file_unique_id
    elif event.sticker:
        file_id = event.sticker.file_id
        unique_id = event.sticker.file_unique_id
    elif event.animation:
        file_id = event.animation.file_id
        unique_id = event.animation.file_unique_id
    elif event.video:
        file_id = event.video.file_id
        unique_id = event.video.file_unique_id

    if not file_id and not unique_id:
        return

    # Fast path: already known NSFW by unique_id or file_id
    if (unique_id and is_nsfw_cached(unique_id)) or (unique_id and await is_nsfw_unique(unique_id)) or (file_id and await is_nsfw(file_id)):
        await send_msg(event)
        return

    try:
        if event.photo:
            file_obj = await client.download_media(event.photo, in_memory=True)
            try:
                file_obj.seek(0)
            except Exception:
                pass
            img = Image.open(file_obj).convert("RGB")
            nsfw = await classify_image_async(img)
            if nsfw:
                if file_id:
                    await add_nsfw(file_id)
                if unique_id:
                    mark_nsfw_cached(unique_id)
                    await add_nsfw_unique(unique_id)
                await send_msg(event)
            else:
                if file_id:
                    await remove_nsfw(file_id)
                if unique_id:
                    mark_safe_cached(unique_id)
                    await remove_nsfw_unique(unique_id)
            return

        elif event.sticker:
            # Handle different sticker types
            mime = event.sticker.mime_type or ""
            if mime == "video/webm" or getattr(event.sticker, "is_video", False):
                # Animated video sticker (webm)
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    await client.download_media(event.sticker, file_name=tmp_path)
                    await classify_video(event, tmp_path, file_id, unique_id)
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                return
            if mime == "application/x-tgsticker" or getattr(event.sticker, "is_animated", False):
                # TGS (Lottie) stickers are vector animations; skip (unsupported)
                return

            # Static sticker (likely .webp)
            file_obj = await client.download_media(event.sticker, in_memory=True)
            try:
                file_obj.seek(0)
            except Exception:
                pass
            img = Image.open(file_obj).convert("RGB")
            nsfw = await classify_image_async(img)
            if nsfw:
                if file_id:
                    await add_nsfw(file_id)
                if unique_id:
                    mark_nsfw_cached(unique_id)
                    await add_nsfw_unique(unique_id)
                await send_msg(event)
            else:
                if file_id:
                    await remove_nsfw(file_id)
                if unique_id:
                    mark_safe_cached(unique_id)
                    await remove_nsfw_unique(unique_id)
            return

        elif event.animation:
            # GIFs are downloaded as MP4
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                await client.download_media(event.animation, file_name=tmp_path)
                await classify_video(event, tmp_path, file_id, unique_id)
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return

        elif event.video:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                await client.download_media(event.video, file_name=tmp_path)
                await classify_video(event, tmp_path, file_id, unique_id)
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            return

    except Exception as e:
        logging.error(f"Failed to process media: {e}")

@client.on_message(filters.command("start"))
async def start(_, event):
    buttons = [[InlineKeyboardButton("Support Chat", url="t.me/VivaanSupport"), InlineKeyboardButton("News Channel", url="t.me/VivaanNetwork")]]
    reply_markup = InlineKeyboardMarkup(buttons)
    await event.reply_text("Hello, I am a bot that detects NSFW (Not Safe for Work) images and stickers. Send me an image to check if it is NSFW or not. In groups, just make me an admin with delete message rights and I will delete all NSFW images sent by anyone.", reply_markup=reply_markup)
    if event.from_user and event.from_user.id:
        username = getattr(event.from_user, "username", None) or "None"
        await add_user(event.from_user.id, username)

async def send_msg(event):
    if event.chat.type in (ChatType.SUPERGROUP, ChatType.GROUP):
        try:
            await event.delete()
        except Exception:
            pass
        try:
            await client.send_message(event.chat.id, "NSFW image detected :)")
        except Exception:
            pass
        await add_chat(event.chat.id)
    else:
        await event.reply("NSFW Image.")

async def classify_video(event, video_path, file_id, unique_id):
    # Prevent reprocessing
    if (unique_id and is_nsfw_cached(unique_id)) or (unique_id and await is_nsfw_unique(unique_id)) or (file_id and await is_nsfw(file_id)):
        await send_msg(event)
        return

    frames = sample_video_frames(video_path)
    try:
        for img in frames:
            nsfw = await classify_image_async(img)
            if nsfw:
                if file_id:
                    await add_nsfw(file_id)
                if unique_id:
                    mark_nsfw_cached(unique_id)
                    await add_nsfw_unique(unique_id)
                await send_msg(event)
                return
        # None of the sampled frames considered NSFW
        if file_id:
            await remove_nsfw(file_id)
        if unique_id:
            mark_safe_cached(unique_id)
            await remove_nsfw_unique(unique_id)
    except Exception as e:
        logging.error(f"Failed to analyze video: {e}")