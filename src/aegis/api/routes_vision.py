from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import pyautogui
import io
import asyncio
from PIL import Image

router = APIRouter(prefix="/vision", tags=["vision"])

def _capture_screen_frame() -> bytes:
    screenshot = pyautogui.screenshot()
    screenshot.thumbnail((1280, 720), Image.Resampling.LANCZOS)

    img_byte_arr = io.BytesIO()
    screenshot.save(img_byte_arr, format='JPEG', quality=60)
    return img_byte_arr.getvalue()

async def generate_screen_frames():
    """Generates JPEG frames of the screen continuously using PyAutoGUI."""
    while True:
        try:
            frame_bytes = await asyncio.to_thread(_capture_screen_frame)

            # Yield frame in multipart format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            
            # Aim for ~10 FPS to avoid overloading the CPU
            await asyncio.sleep(0.1)
        except Exception as e:
            # Log error and try again
            await asyncio.sleep(1)

@router.get("/stream")
async def video_feed():
    """Live MJPEG video feed of the desktop screen."""
    return StreamingResponse(
        generate_screen_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )
