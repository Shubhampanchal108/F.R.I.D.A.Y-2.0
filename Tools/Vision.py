import os
import sys
import io
import json
import base64
from io import BytesIO

# Reconfigure stdout for UTF-8
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pyautogui
from PIL import Image

# Ensure parent path is in sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    from config.config_driver import Check_Keys
except ImportError:
    from config.config_driver import Check_Keys


def _get_gemini_client():
    """Returns an authenticated google.genai Client using configured GEMINI_KEY."""
    try:
        from google import genai
        # 1. Check config.json under KEYS -> GEMINI_KEY
        key = Check_Keys("KEYS", "GEMINI_KEY")
        if not key or not str(key).strip().startswith("AIza"):
            # 2. Check environment variables
            key = os.environ.get("GEMINI_KEY") or os.environ.get("GEMINI_API_KEY")
        if key and str(key).strip().startswith("AIza"):
            return genai.Client(api_key=str(key).strip())
    except Exception as e:
        print(f"⚠️ Gemini Client init warning: {e}")
    return None


def capture_screen_image() -> Image.Image:
    """Captures current desktop screen and returns a PIL Image."""
    # 1. Try mss (fastest and most reliable on Windows)
    try:
        import mss
        with mss.mss() as sct:
            monitor = sct.monitors[1] if len(sct.monitors) > 1 else sct.monitors[0]
            shot = sct.grab(monitor)
            return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
    except Exception:
        pass

    # 2. Try PIL ImageGrab
    try:
        from PIL import ImageGrab
        img = ImageGrab.grab()
        if img:
            return img
    except Exception:
        pass

    # 3. Try pyautogui
    try:
        return pyautogui.screenshot()
    except Exception as e:
        print(f"⚠️ Screen capture error: {e}")
        return None


def capture_screen_base64() -> str:
    """Captures desktop screen and returns Base64 encoded JPEG string."""
    try:
        screenshot = capture_screen_image()
        if not screenshot:
            return None
        buffer = BytesIO()
        screenshot.save(buffer, format="JPEG", quality=85)
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        print(f"⚠️ Base64 screenshot error: {e}")
        return None


def capture_camera_image() -> Image.Image:
    """Captures a single frame from the primary webcam using OpenCV."""
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            return None
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb_frame)
    except Exception as e:
        print(f"⚠️ Camera capture error: {e}")
        return None


GEMINI_CASCADE_MODELS = [
    "models/gemini-3.5-flash-lite",
    "models/gemini-3.1-flash-lite",
    "models/gemini-2.5-flash",
    "models/gemini-flash-latest",
]

OPENROUTER_FREE_VISION_MODELS = [
    "nvidia/nemotron-nano-12b-v2-vl:free",
    "google/gemma-3-27b-it:free",
    "meta-llama/llama-3.2-11b-vision-instruct:free",
]


def query_vision_model(prompt: str, image: Image.Image | None = None) -> str:
    """
    Bulletproof multi-model cascade for multimodal vision & text generation.
    1. Tries active Google Gemini flash models (gemini-3.5-flash-lite, gemini-3.1-flash-lite, etc.)
    2. Automatically catches 429 RESOURCE_EXHAUSTED / quota / 503 errors and fails over to next model.
    3. If all Google models fail or hit quota, immediately fails over to OpenRouter Free Vision models.
    """
    # 1. Google Gemini Model Cascade
    client = _get_gemini_client()
    if client:
        for model_name in GEMINI_CASCADE_MODELS:
            try:
                contents = [prompt]
                if image is not None:
                    contents.append(image)

                response = client.models.generate_content(
                    model=model_name,
                    contents=contents
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                err_str = str(e).lower()
                if any(x in err_str for x in ["429", "resource_exhausted", "quota", "503", "404"]):
                    print(f"[Vision Cascade] ⚠️ Model '{model_name}' hit rate limit/error. Failing over to next model...")
                    continue
                else:
                    print(f"[Vision Cascade] ⚠️ Model '{model_name}' error: {e}")
                    continue

    # 2. OpenRouter Free Vision Fallback Failover
    try:
        from openai import OpenAI
        openrouter_key = Check_Keys("KEYS", "OPENROUTER_KEY")
        if not openrouter_key:
            # Fallback to J.A.R.V.I.S api_keys.json if present
            try:
                jarvis_cfg = os.path.join(os.path.dirname(__file__), "..", "J.A.R.V.I.S", "config", "api_keys.json")
                if os.path.exists(jarvis_cfg):
                    with open(jarvis_cfg, "r", encoding="utf-8") as f:
                        openrouter_key = json.load(f).get("openrouter_api_key", "")
            except Exception:
                pass

        if openrouter_key:
            or_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=openrouter_key
            )

            # Prepare base64 image if image is provided
            content_payload = [{"type": "text", "text": prompt}]
            if image is not None:
                buf = BytesIO()
                image.save(buf, format="JPEG", quality=80)
                b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                content_payload.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

            for or_model in OPENROUTER_FREE_VISION_MODELS:
                try:
                    res = or_client.chat.completions.create(
                        model=or_model,
                        messages=[{"role": "user", "content": content_payload}],
                        max_tokens=600,
                        timeout=20.0
                    )
                    text = res.choices[0].message.content.strip() if res.choices else ""
                    if text:
                        print(f"[Vision Failover] ✅ OpenRouter model '{or_model}' handled visual query successfully.")
                        return text
                except Exception as or_err:
                    print(f"[Vision Failover] ⚠️ OpenRouter '{or_model}' note: {or_err}")
                    continue
    except Exception as e:
        print(f"[Vision Failover] ⚠️ OpenRouter fallback error: {e}")

    # 3. Fallback to 4-Tier Neural Core if no image required
    try:
        if not image:
            from core.llm_router import chat_complete
            res = chat_complete(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500
            )
            return res.strip()
    except Exception:
        pass

    return ""


def analyze_screen(prompt: str = "Analyze what is on the screen and describe visible UI elements, code errors, or documents clearly."):
    """
    Captures current desktop screen and analyzes it using the bulletproof Vision Cascade.
    """
    screenshot = capture_screen_image()
    if not screenshot:
        return "❌ Sir, failed to capture desktop screen image."

    full_prompt = (
        f"You are F.R.I.D.A.Y, personal AI assistant to Shubham sir.\n"
        f"User Request: {prompt}\n"
        f"Please inspect the provided desktop screenshot carefully. "
        f"Identify any code, error messages, active applications, or text, "
        f"and provide a concise, direct, and actionable explanation for Shubham sir."
    )

    result = query_vision_model(prompt=full_prompt, image=screenshot)
    if result:
        return result

    return "❌ Sir, unable to process the screen with available vision models. Please verify your GEMINI_KEY."


def analyze_camera(prompt: str = "Analyze what is visible in front of the webcam."):
    """
    Captures a frame from the user's webcam and analyzes it using Gemini Flash.
    """
    cam_img = capture_camera_image()
    if not cam_img:
        return "❌ Sir, could not access or capture image from the webcam. Please verify camera permissions."

    client = _get_gemini_client()
    if client:
        try:
            full_prompt = (
                f"You are F.R.I.D.A.Y, personal AI assistant to Shubham sir.\n"
                f"User Camera Request: {prompt}\n"
                f"Inspect what is in front of the camera and describe it clearly and respectfully."
            )
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[full_prompt, cam_img]
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            return f"❌ Camera analysis error: {e}"

    return "❌ Sir, Gemini vision client is unavailable for camera analysis."


def analyze_clipboard(prompt: str = "Analyze the code error or text in clipboard and provide a complete working fix."):
    """
    Reads text from user's clipboard and uses Gemini to diagnose code errors, summarize text, or explain tracebacks.
    """
    try:
        import pyperclip
        clip_text = pyperclip.paste()
        if not clip_text or not clip_text.strip():
            return "❌ Clipboard is currently empty, Sir."

        client = _get_gemini_client()
        if client:
            full_prompt = (
                f"You are F.R.I.D.A.Y, personal AI assistant to Shubham sir.\n"
                f"Clipboard Content:\n```\n{clip_text[:4000]}\n```\n"
                f"User Request: {prompt}\n"
                f"Provide a clear, direct, and fully solved explanation or code fix for Shubham sir."
            )
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt
            )
            if res and res.text:
                return res.text.strip()
        return f"Clipboard Content:\n{clip_text[:500]}"
    except Exception as e:
        return f"❌ Clipboard analysis error: {e}"


def start_live_vision(mode: str = "screen"):
    """
    Activates FRIDAY's real-time multimodal streaming mode.
    mode: 'screen' (to see desktop screen in real-time) or 'camera' (to access webcam in real-time).
    """
    try:
        from Live_mode import run_live_mode
        chosen = "camera" if "cam" in str(mode).lower() else "screen"
        run_live_mode(video_mode=chosen)
        return f"Sir, live vision streaming mode ({chosen}) has concluded successfully."
    except Exception as e:
        return f"Sir, encountered an error launching live mode: {e}"


if __name__ == "__main__":
    print("📸 Testing Screen Vision Analysis with Gemini Flash...")
    res = analyze_screen("What application is currently open on my screen? Give a 1-sentence answer.")
    print("\nResult:\n", res)
