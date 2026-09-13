import os
import sys
import json
from openai import OpenAI

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


def build_client_pool(config: dict) -> list:
    """
    Construye la lista de cuentas/API keys utilizables, en el orden en que
    se probarán al traducir o verificar: primero la cuenta activa, luego el
    resto de perfiles que tengan una API key rellenada. Los perfiles sin
    API key se ignoran.

    Vive aquí (y no en la UI) para que tanto la ventana principal como el
    diálogo de gestión de cuentas puedan usarla sin depender la una de la
    otra.

    Devuelve una lista de dicts: {"name": str, "client": OpenAI, "model": str}
    """
    pool = []
    profiles = config.get("profiles", {})
    active = config.get("active_profile")

    ordered_names = []
    if active in profiles:
        ordered_names.append(active)
    ordered_names += [name for name in profiles if name != active]

    for name in ordered_names:
        data = profiles.get(name, {})
        api_key = data.get("api_key", "").strip()
        if not api_key:
            continue
        try:
            client = OpenAI(api_key=api_key, base_url=data.get("base_url") or None)
        except Exception:
            continue
        pool.append({
            "name": name,
            "client": client,
            "model": data.get("model", "gemini-3.6-flash")
        })

    return pool