import os
import tkinter as tk
from tkinter import ttk

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMG_DIR = os.path.join(BASE_DIR, "img")
IMG_LETRAS_PATH = os.path.join(IMG_DIR, "guxing-letras.png")
IMG_ICO_PATH = os.path.join(IMG_DIR, "guxing-ico.png")

# Rutas a los nuevos iconos de los botones
IMG_BUTTONS_DIR = os.path.join(IMG_DIR, "buttons")
IMG_BTN_LIBROS = os.path.join(IMG_BUTTONS_DIR, "libros.png")
IMG_BTN_TRADUCCION = os.path.join(IMG_BUTTONS_DIR, "traduccion.png")
IMG_BTN_APIKEY = os.path.join(IMG_BUTTONS_DIR, "apikey.png")
IMG_BTN_EXIT = os.path.join(IMG_BUTTONS_DIR, "exit.png")

DARK_RUGRATS = {
    "bg_dark": "#121422",              # Fondo espacial oscuro profundo
    "panel_dark": "#1b1e33",           # Fondo de tarjetas y paneles
    "drop_bg": "#151829",              # Fondo de campos de texto, inputs y drop zone
    "tommy_blue": "#00b4d8",           # Azul Tommy Pickles
    "tommy_blue_hover": "#0096c7",
    "chuckie_orange": "#ff5400",       # Naranja Chuckie Finster
    "chuckie_orange_hover": "#e04800",
    "chuckie_yellow": "#ffd166",       # Amarillo retro
    "angelica_purple": "#9d4edd",      # Morado Angélica
    "angelica_purple_hover": "#7b2cbf",
    "reptar_green": "#06d6a0",         # Verde Reptar
    "reptar_green_hover": "#05b386",
    "border_comic": "#2e3458",         # Borde estilo cómic
    "text_light": "#f8f9fa",           # Texto principal claro
    "text_muted": "#94a3b8"            # Texto secundario/atenuado
}

def apply_rugrats_theme(root: tk.Tk):
    """Aplica la estética moderna Dark Rugrats a todos los widgets ttk."""
    style = ttk.Style(root)
    style.theme_use("clam")

    # --- Treeview (Árbol de Estudio) ---
    style.configure(
        "Treeview",
        background=DARK_RUGRATS["drop_bg"],
        foreground=DARK_RUGRATS["text_light"],
        fieldbackground=DARK_RUGRATS["drop_bg"],
        borderwidth=0,
        font=("Helvetica", 10),
        rowheight=28
    )
    style.map(
        "Treeview",
        background=[("selected", DARK_RUGRATS["tommy_blue"])],
        foreground=[("selected", "#ffffff")]
    )

    style.configure(
        "Treeview.Heading",
        background=DARK_RUGRATS["panel_dark"],
        foreground=DARK_RUGRATS["chuckie_yellow"],
        relief="flat",
        font=("Helvetica", 10, "bold"),
        borderwidth=1,
        bordercolor=DARK_RUGRATS["border_comic"]
    )
    style.map(
        "Treeview.Heading",
        background=[("active", DARK_RUGRATS["border_comic"])]
    )

    # --- Combobox (Desplegables) ---
    style.configure(
        "TCombobox",
        fieldbackground=DARK_RUGRATS["drop_bg"],
        background=DARK_RUGRATS["border_comic"],
        foreground=DARK_RUGRATS["text_light"],
        arrowcolor=DARK_RUGRATS["tommy_blue"],
        relief="flat",
        borderwidth=1,
        bordercolor=DARK_RUGRATS["border_comic"]
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", DARK_RUGRATS["drop_bg"])],
        selectbackground=[("readonly", DARK_RUGRATS["tommy_blue"])],
        selectforeground=[("readonly", "#ffffff")]
    )

    # --- Entry (Campos de Texto) ---
    style.configure(
        "TEntry",
        fieldbackground=DARK_RUGRATS["drop_bg"],
        foreground=DARK_RUGRATS["text_light"],
        relief="flat",
        borderwidth=1,
        bordercolor=DARK_RUGRATS["border_comic"]
    )

    # --- Progressbar ---
    style.configure(
        "Horizontal.TProgressbar",
        troughcolor=DARK_RUGRATS["drop_bg"],
        background=DARK_RUGRATS["chuckie_orange"],
        bordercolor=DARK_RUGRATS["border_comic"],
        lightcolor=DARK_RUGRATS["chuckie_yellow"],
        darkcolor=DARK_RUGRATS["chuckie_orange"]
    )