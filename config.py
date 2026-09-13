import os
import sys
import json
import subprocess
import shutil
from openai import OpenAI

TEMPLATES = {
    "Google Gemini (100% Gratis)": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "model": "gemini-1.5-flash"
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

def get_app_dir() -> str:
    """Devuelve el directorio base de datos de Guxing en el sistema."""
    if sys.platform == "win32":
        base_dir = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base_dir = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    app_dir = os.path.join(base_dir, "guxing")
    os.makedirs(app_dir, exist_ok=True)
    return app_dir

CONFIG_FILE = os.path.join(get_app_dir(), "config.json")
LIBRARY_FILE = os.path.join(get_app_dir(), "library.json")
LIBRARY_BASE_DIR = os.path.join(get_app_dir(), "biblioteca")
os.makedirs(LIBRARY_BASE_DIR, exist_ok=True)

def open_folder_in_file_manager(target_path: str):
    """Abre una carpeta o archivo en el explorador de archivos nativo del SO."""
    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
        
    folder = target_path if os.path.isdir(target_path) else os.path.dirname(target_path)
    
    if sys.platform == "win32":
        os.startfile(folder)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", folder])
    else:
        # Linux (Nautilus, Dolphin, etc.)
        subprocess.Popen(["xdg-open", folder])

def get_topic_folder(course_name: str, subject_name: str, topic_name: str) -> str:
    """Crea y devuelve la ruta física en disco para un tema específico."""
    def sanitize(name: str) -> str:
        return "".join(c for c in name if c.isalnum() or c in (' ', '_', '-', 'º', 'ª')).strip()
    
    path = os.path.join(
        LIBRARY_BASE_DIR,
        sanitize(course_name),
        sanitize(subject_name),
        sanitize(topic_name)
    )
    os.makedirs(path, exist_ok=True)
    return path

# ----------------- CONFIGURACIÓN Y APIS -----------------

def load_config() -> dict:
    default_config = {
        "active_profile": "Google Gemini (100% Gratis)",
        "profiles": {
            "Google Gemini (100% Gratis)": {
                "api_key": "",
                "base_url": TEMPLATES["Google Gemini (100% Gratis)"]["base_url"],
                "model": "gemini-1.5-flash"
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
            "model": data.get("model", "gemini-1.5-flash")
        })
    return pool

# ----------------- GESTIÓN DE BIBLIOTECA -----------------

def load_library() -> dict:
    default_lib = {"courses": []}
    if not os.path.exists(LIBRARY_FILE):
        return default_lib
    try:
        with open(LIBRARY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_lib

def save_library(library_data: dict):
    with open(LIBRARY_FILE, "w", encoding="utf-8") as f:
        json.dump(library_data, f, indent=2, ensure_ascii=False)