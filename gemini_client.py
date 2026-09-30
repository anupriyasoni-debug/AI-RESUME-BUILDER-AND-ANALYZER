import os

try:
    import google.generativeai as genai
except ImportError:
    genai = None
from dotenv import load_dotenv


DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"

load_dotenv()


def create_gemini_model():
    if genai is None:
        raise ImportError("google-generativeai is not installed. Run 'pip install google-generativeai'.")
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in {"your_key_here", "your_gemini_api_key_here"}:
        raise ValueError("Gemini is not configured. Add GEMINI_API_KEY to your local .env file.")

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    return model_name, genai.GenerativeModel(model_name)
