import cv2
from PIL import Image
import torch
from transformers import AutoModelForImageClassification, AutoImageProcessor
import os

model = AutoModelForImageClassification.from_pretrained("Falconsai/nsfw_image_detection")
processor = AutoImageProcessor.from_pretrained("Falconsai/nsfw_image_detection")
model.eval()

def getimage():
    print("Enter the file path of the image or video: ")
    path = input().strip()
    if not path:
        print("No path provided.")
        return

    lower = path.lower()
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        try:
            img = Image.open(path).convert("RGB")
        except Exception as e:
            print("Invalid file path. Error:", e)
            return
        with torch.no_grad():
            inputs = processor(images=img, return_tensors="pt")
            outputs = model(**inputs)
            logits = outputs.logits

        predicted_label = logits.argmax(-1).item()
        print("NSFW" if predicted_label else "Not NSFW")
    
    elif lower.endswith((".mp4", ".webm")):
        classify_video(path)
    
    else:
        print("Invalid file format")

def sample_video_frames(path, seconds_interval=10, max_frames=5):
    cap = cv2.VideoCapture(path)
    frames = []
    try:
        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 25.0
        frame_interval = int(fps * seconds_interval)
        if frame_interval <= 0:
            frame_interval = int(fps * 10) or 250

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        frame_indices = []
        for i in range(max_frames):
            idx = i * frame_interval
            if total_frames and idx >= total_frames:
                break
            frame_indices.append(idx)

        if not frame_indices:
            frame_indices = [0]

        for idx in frame_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            success, frame = cap.read()
            if not success or frame is None:
                continue
            image_name = f"frame_{idx}.png"
            cv2.imwrite(image_name, frame)
            frames.append(image_name)
            if len(frames) >= max_frames:
                break
    finally:
        cap.release()
    return frames

def classify_video(video_path):
    image_names = sample_video_frames(video_path)
    if not image_names:
        print("Could not extract frames from the video.")
        return
    try:
        any_nsfw = False
        for name in image_names:
            try:
                img = Image.open(name).convert("RGB")
            except Exception:
                continue
            with torch.no_grad():
                inputs = processor(images=img, return_tensors="pt")
                outputs = model(**inputs)
                logits = outputs.logits

            predicted_label = logits.argmax(-1).item()
            if predicted_label:
                any_nsfw = True
                break
        print("NSFW" if any_nsfw else "Not NSFW")
    finally:
        for name in image_names:
            try:
                os.remove(name)
            except Exception:
                pass

if __name__ == "__main__":
    getimage()