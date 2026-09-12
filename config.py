# config.py
from pathlib import Path
from dotenv import load_dotenv
import os

# 1. Dynamically detect project root
PROJECT_ROOT = Path(__file__).resolve().parent

ENV_PATH = PROJECT_ROOT / '.env'

# 2. Load .env if it exists (local development)
if ENV_PATH.exists():
    load_dotenv(dotenv_path=str(ENV_PATH), override=True)

# 3. Get OpenRouter API key (from env or Streamlit secrets)
def get_openrouter_key():
    """Fetch OPENROUTER_API_KEY from environment or Streamlit secrets."""
    # Try environment variable first (local .env)
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key
    # Try Streamlit secrets (Streamlit Cloud / Hugging Face Spaces)
    try:
        import streamlit as st
        if "OPENROUTER_API_KEY" in st.secrets:
            return st.secrets["OPENROUTER_API_KEY"]
    except Exception:
        pass
    return None

OPENROUTER_API_KEY = get_openrouter_key()
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

def get_model_path(model_name: str):
    return PROJECT_ROOT / 'models' / model_name
