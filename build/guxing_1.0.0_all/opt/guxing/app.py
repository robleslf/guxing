import tkinter as tk
from ui.main_window import TranslatorApp

try:
    from tkinterdnd2 import TkinterDnD
    HAS_DND = True
except ImportError:
    HAS_DND = False

if __name__ == "__main__":
    if HAS_DND:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()

    # Fija el WM_CLASS para que el gestor de ventanas de Linux (GNOME/KDE/etc.)
    # asocie esta ventana con la entrada .desktop "guxing" y muestre su icono
    # en la barra de tareas/dock en lugar del engranaje genérico de Python.
    try:
        root.wm_class("guxing", "Guxing")
    except Exception:
        pass

    app = TranslatorApp(root)
    root.mainloop()