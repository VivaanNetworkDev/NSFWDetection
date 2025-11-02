import cv2
import os
import logging
import asyncio
import tempfile
import io
from PIL import Image
import torch
from telegram import client
from pyrogram import filters
from telegram.db import is_nsfw, add_chat, add_user, add_nsfw, remove_nsfw
from transformers import AutoModelForImageClassification, ViTImageProcessor
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Load model and processor once at import time
model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
processor = ViTImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")

def predict_is_nsfw(image: Image.Image) -> bool:
    """Synchronous prediction; returns True if NSFW."""
    with torch.no_grad():
        inputs = processor(images=image, return_tensors="pt")
        outputs = model(**inputs)
        logits = outputs.logits
    return bool(logits.argmax(-1).item())

async def classify_image_async(image: Image.Image) -> bool:
    """Run classification in a thread to avoid blocking the event loop."""
    return await asyncio.to_thread(predict_is_nsfw, image)

def sample_video_frames(path: str, sample_seconds=(0, 10, 20), max_frames=3):
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
            if not success:
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
    # Determine file_id
    file_id = None
    if event.photo:
        file_id = event.photo.file_id
    elif event.sticker:
        file_id = event.sticker.file_id
    elif event.animation:
        file_id = event.animation.file_id
    elif event.video:
        file_id = event.video.file_id

    if not file_id:
        return

    # Skip if already marked as NSFW
    if await is_nsfw(file_id):
        await send_msg(event)
        return

    try:
        if event.photo:
            buf = io.BytesIO()
            await client.download_media(event.photo, file_name=buf)
            buf.seek(0)
            img = Image.open(buf).convert("RGB")
            nsfw = await classify_image_async(img)
            if nsfw:
                await add_nsfw(file_id)
                await send_msg(event)
            else:
                await remove_nsfw(file_id)
            return

        elif event.sticker:
            if event.sticker.mime_type == "video/webm":
                # Animated sticker (video/webm)
                with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
                    tmp_path = tmp.name
                try:
                    await client.download_media(event.sticker, file_name=tmp_path)
                    await videoShit(event, tmp_path, file_id)
                finally:
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                return
            else:
                # Static sticker (likely .webp)
                buf = io.BytesIO()
                await client.download_media(event.sticker, file_name=buf)
                buf.seek(0)
                img = Image.open(buf).convert("RGB")
                nsfw = await classify_image_async(img)
                if nsfw:
                    await add_nsfw(file_id)
                    await send_msg(event)
                else:
                    await remove_nsfw(file_id)
                return

        elif event.animation:
            # GIFs are downloaded as MP4
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                await client.download_media(event.animation, file_name=tmp_path)
                await videoShit(event, tmp_path, file_id)
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
                await videoShit(event, tmp_path, file_id)
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
    if event.from_user.username:
        await add_user(event.from_user.id, event.from_user.username)
    else:
        await add_user(event.from_user.id, "None")

async def send_msg(event):
    if event.chat.type == ChatType.SUPERGROUP:
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

async def videoShit(event, video_path, file_id):
    # Prevent reprocessing
    if await is_nsfw(file_id):
        await send_msg(event)
        return

    frames = sample_video_frames(video_path)
    try:
        for img in frames:
            nsfw = await classify_image_async(img)
            if nsfw:
                await add_nsfw(file_id)
                await send_msg(event)
                return
        # None of the sampled frames considered NSFW
        await remove_nsfw(file_id)
    except Exception as e:
        logging.error(f"Failed to analyze video: {e}")