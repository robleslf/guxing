import sys
import os
import subprocess
import venv
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE_DIR, ".venv")

# Librerías necesarias mapeadas a su nombre de importación
REQUIRED_PACKAGES = {
    "openai": "openai",
    "pymupdf": "pymupdf",
    "pypdf": "pypdf",
    "python-docx": "docx",
    "odfpy": "odf",
    "pillow": "PIL",
    "tkinterdnd2": "tkinterdnd2"
}


def get_secure_config_path() -> str:
    """Calcula la ruta segura en el sistema (~/.config en Linux o %APPDATA% en Windows)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    app_dir = os.path.join(base, "guxing")
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, "config.json")


def self_heal_security_and_git():
    """El programa comprueba y soluciona problemas de seguridad y Git por sí mismo."""
    secure_cfg = get_secure_config_path()
    local_cfg = os.path.join(BASE_DIR, "config.json")

    # 1. Si existe un config.json local en el proyecto, lo mueve a la zona segura y borra el local
    if os.path.exists(local_cfg):
        try:
            if not os.path.exists(secure_cfg):
                shutil.move(local_cfg, secure_cfg)
            else:
                os.remove(local_cfg)
        except Exception:
            pass

    # 2. Asegura permisos 0600 en Linux/Mac de forma silenciosa
    if os.path.exists(secure_cfg) and sys.platform != "win32":
        try:
            os.chmod(secure_cfg, 0o600)
        except Exception:
            pass

    # 3. Crea el .gitignore automáticamente si no existe para proteger el repositorio
    gitignore_path = os.path.join(BASE_DIR, ".gitignore")
    if not os.path.exists(gitignore_path):
        try:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write(".venv/\n__pycache__/\n*.pyc\nconfig.json\n*.env\n*_Bilingue.html\n.DS_Store\n")
        except Exception:
            pass


def get_venv_python():
    if sys.platform == "win32":
        return os.path.join(VENV_DIR, "Scripts", "python.exe")
    return os.path.join(VENV_DIR, "bin", "python")


def ensure_venv():
    if not os.path.exists(VENV_DIR):
        print("Preparando el entorno por primera vez (esto solo ocurrirá una vez)...")
        venv.create(VENV_DIR, with_pip=True)


def install_dependencies():
    python_exe = get_venv_python()
    for pkg_name, import_name in REQUIRED_PACKAGES.items():
        try:
            subprocess.check_call(
                [python_exe, "-c", f"import {import_name}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except subprocess.CalledProcessError:
            print(f"Instalando componente: {pkg_name}...")
            subprocess.check_call([python_exe, "-m", "pip", "install", pkg_name, "--quiet"])


def launch_main_app():
    python_exe = get_venv_python()
    main_script = os.path.join(BASE_DIR, "app.py")
    subprocess.run([python_exe, main_script])


if __name__ == "__main__":
    # Nota: esto es solo para ejecutar Guxing directamente desde el código
    # fuente durante el desarrollo. Para una instalación normal de usuario
    # (con icono en el menú de aplicaciones y en la barra de tareas), usa
    # ./install.sh una sola vez.
    self_heal_security_and_git()
    ensure_venv()
    install_dependencies()
    launch_main_app()