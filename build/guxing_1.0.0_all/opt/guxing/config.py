import os
import sys
import json

TEMPLATES = {
    "Google Gemini (100% Gratis)": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-3.6-flash"
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "model": "deepseek-chat"
    },
    "Groq (100% Gratis)": {
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile"
    },
    "OpenAI": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    },
    "Personalizado": {
        "base_url": "",
        "model": ""
    }
}

def get_secure_config_path() -> str:
    """Devuelve la ruta segura en el sistema operativo."""
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))

    app_dir = os.path.join(base_dir, "guxing")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "config.json")

CONFIG_FILE = get_secure_config_path()

def load_config() -> dict:
    default_config = {
        "active_profile": "Google Gemini (100% Gratis)",
        "profiles": {
            "Google Gemini (100% Gratis)": {
                "api_key": "",
                "base_url": TEMPLATES["Google Gemini (100% Gratis)"]["base_url"],
                "model": "gemini-3.6-flash"
            }
        }
    }

    if not os.path.exists(CONFIG_FILE):
        return default_config

    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_config

def save_config(config: dict):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
        
    if sys.platform != "win32":
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except Exception:
            pass