import os
import sys
import base64
from io import BytesIO

# UTF-8 stdout reconfigure for Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

import pyautogui

# Parent path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from openai import OpenAI
from config_driver import Check_Keys


def capture_screen_base64():
    """Captures desktop screen and returns Base64 encoded JPEG string."""
    try:
        screenshot = pyautogui.screenshot()
        buffer = BytesIO()
        screenshot.save(buffer, format="JPEG", quality=80)
        encoded_image = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return encoded_image
    except Exception as e:
        print(f"⚠️ Screenshot capture error: {e}")
        return None


def analyze_screen(prompt: str = "Analyze what is on the screen and describe visible UI elements, code errors, or documents clearly."):
    """
    Captures current desktop screen and sends it to Vision LLM for analysis.
    Useful for debugging code on screen, reading documents, or explaining UI.
    """
    img_b64 = capture_screen_base64()
    if not img_b64:
        return "❌ Failed to capture screen image."

    llm_key = Check_Keys("KEYS", "LLM_KEY")
    base_url = Check_Keys("LLM", "LLM_SERVICE_PROVIDER_URL")
    model = Check_Keys("LLM", "MODEL")

    client = OpenAI(
        base_url=base_url if base_url else None,
        api_key=llm_key
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": f"Screen Analysis Request: {prompt}\nDescribe clearly and concisely for Shubham sir."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img_b64}"
                    }
                }
            ]
        }
    ]

    # Models to attempt in order of priority
    candidate_models = [model]
    
    # Provider-specific vision model fallbacks
    if "openrouter" in (base_url or "").lower():
        candidate_models.extend([
            "openai/gpt-4o-mini",
            "google/gemini-flash-1.5",
            "meta-llama/llama-3.2-11b-vision-instruct",
            "qwen/qwen-2.5-vl-72b-instruct:free"
        ])
    elif "openai" in (base_url or "").lower() or not base_url:
        candidate_models.extend(["gpt-4o-mini", "gpt-4o"])

    last_error = None
    for m in candidate_models:
        if not m:
            continue
        try:
            response = client.chat.completions.create(
                model=m,
                messages=messages,
                max_tokens=600
            )
            answer = response.choices[0].message.content.strip()
            if answer:
                return answer
        except Exception as e:
            last_error = str(e)
            continue

    return f"❌ Screen Analysis Error: Could not analyze screen image with model '{model}'. Details: {last_error}. You can update your vision model in /config."


if __name__ == "__main__":
    print("📸 Testing Screen Vision Analysis...")
    res = analyze_screen("What application is open on screen?")
    print(res)
