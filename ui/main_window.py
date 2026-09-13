import os
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from config import load_config, save_config, build_client_pool
from core.parser import extract_text_from_file
from core.translator import translate_blocks_batch, check_client_pool
from core.viewer_html import generate_html_viewer
from ui.theme import DARK_RUGRATS, IMG_LETRAS_PATH, IMG_ICO_PATH
from ui.api_dialog import ApiManagerDialog

try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False


def load_resized_image(path, target_height=180):
    try:
        from PIL import Image, ImageTk
        img = Image.open(path)
        w, h = img.size
        ratio = target_height / float(h)
        new_w = int(w * ratio)
        img = img.resize((new_w, target_height), Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        raw_img = tk.PhotoImage(file=path)
        h = raw_img.height()
        if h > target_height:
            factor = max(1, round(h / target_height))
            return raw_img.subsample(factor, factor)
        return raw_img


class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 GUXING")
        self.root.configure(bg=DARK_RUGRATS["bg_dark"])
        self.selected_file_path = None
        self.is_processing = False
        self.is_verifying = False

        if os.path.exists(IMG_ICO_PATH):
            try:
                self.app_icon = tk.PhotoImage(file=IMG_ICO_PATH)
                self.root.iconphoto(True, self.app_icon)
            except Exception:
                pass

        self.maximize_window()
        self.config = load_config()

        main_frame = tk.Frame(root, bg=DARK_RUGRATS["bg_dark"], padx=36, pady=24)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Cabecera
        header_frame = tk.Frame(main_frame, bg=DARK_RUGRATS["bg_dark"])
        header_frame.pack(fill=tk.X, pady=(0, 10))
        tk.Label(header_frame, text="🌐 GUXING", font=("Helvetica", 24, "bold"),
                 bg=DARK_RUGRATS["bg_dark"], fg=DARK_RUGRATS["tommy_blue"]).pack(side=tk.LEFT)
        tk.Label(header_frame, text="Español / Galego ➔ 中文 | Retención de Términos de Examen",
                 font=("Helvetica", 11, "bold"), bg=DARK_RUGRATS["bg_dark"],
                 fg=DARK_RUGRATS["text_muted"]).pack(side=tk.LEFT, padx=16)

        # Barra de cuentas
        prov_bar = tk.Frame(main_frame, bg=DARK_RUGRATS["panel_dark"], bd=2, relief="groove", padx=16, pady=8)
        prov_bar.pack(fill=tk.X, pady=(0, 12))
        tk.Label(prov_bar, text="Cuenta / IA activa:", font=("Helvetica", 11, "bold"),
                 bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"]).pack(side=tk.LEFT)
        self.active_prof_var = tk.StringVar(value=self.config["active_profile"])
        self.cb_active_prof = ttk.Combobox(prov_bar, textvariable=self.active_prof_var,
                                            values=list(self.config["profiles"].keys()), state="readonly", width=28)
        self.cb_active_prof.pack(side=tk.LEFT, padx=6)
        self.cb_active_prof.bind("<<ComboboxSelected>>", self.on_change_active_profile)
        tk.Button(prov_bar, text="⚙ Gestionar APIs", font=("Helvetica", 10, "bold"),
                  bg=DARK_RUGRATS["angelica_purple"], fg="white", relief="flat", padx=10, pady=4,
                  command=self.open_api_manager).pack(side=tk.LEFT, padx=6)
        self.btn_verify = tk.Button(
            prov_bar, text="🔎 Verificar cuentas", font=("Helvetica", 10, "bold"),
            bg=DARK_RUGRATS["tommy_blue"], fg="white", relief="flat", padx=10, pady=4,
            command=self.verify_accounts_manual
        )
        self.btn_verify.pack(side=tk.LEFT, padx=6)

        # Drop Zone
        self.drop_frame = tk.Frame(main_frame, bg=DARK_RUGRATS["drop_bg"], bd=3, relief="ridge",
                                    highlightthickness=2, highlightbackground=DARK_RUGRATS["border_comic"])
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        if os.path.exists(IMG_LETRAS_PATH):
            try:
                self.logo_letras_img = load_resized_image(IMG_LETRAS_PATH, target_height=180)
                self.drop_label_icon = tk.Label(self.drop_frame, image=self.logo_letras_img, bg=DARK_RUGRATS["drop_bg"])
                self.drop_label_icon.pack(expand=True, pady=(16, 2))
            except Exception:
                self.drop_label_icon = tk.Label(self.drop_frame, text="📄", font=("Helvetica", 48),
                                                 bg=DARK_RUGRATS["drop_bg"], fg=DARK_RUGRATS["text_light"])
                self.drop_label_icon.pack(expand=True, pady=(16, 2))
        else:
            self.drop_label_icon = tk.Label(self.drop_frame, text="📄", font=("Helvetica", 48),
                                             bg=DARK_RUGRATS["drop_bg"], fg=DARK_RUGRATS["text_light"])
            self.drop_label_icon.pack(expand=True, pady=(16, 2))

        self.drop_label_text = tk.Label(
            self.drop_frame,
            text="Arrastra aquí tus apuntes (PDF, Word, ODT, TXT)\no haz clic sobre este recuadro para seleccionarlos",
            font=("Helvetica", 13, "bold"),
            fg=DARK_RUGRATS["text_light"],
            bg=DARK_RUGRATS["drop_bg"]
        )
        self.drop_label_text.pack(expand=True, pady=(0, 18))

        self.drop_frame.bind("<Button-1>", lambda e: self.select_file())
        self.drop_label_icon.bind("<Button-1>", lambda e: self.select_file())
        self.drop_label_text.bind("<Button-1>", lambda e: self.select_file())

        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_file_dropped)

        # Botón de confirmación / inicio de traducción (Inicialmente deshabilitado)
        self.btn_start = tk.Button(
            main_frame,
            text="🚀 INICIAR TRADUCCIÓN BILINGÜE",
            font=("Helvetica", 12, "bold"),
            bg="#2e3458",
            fg=DARK_RUGRATS["text_muted"],
            state=tk.DISABLED,
            relief="flat",
            pady=10,
            cursor="arrow",
            command=self.on_start_clicked
        )
        self.btn_start.pack(fill=tk.X, pady=(6, 4))

        # Estado y progreso
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.lbl_status = tk.Label(main_frame, text="Selecciona o arrastra un archivo para comenzar.",
                                    bg=DARK_RUGRATS["bg_dark"], fg=DARK_RUGRATS["text_muted"])
        self.lbl_status.pack(pady=4)

    def maximize_window(self):
        try:
            self.root.attributes('-zoomed', True)
        except Exception:
            try:
                self.root.state('zoomed')
            except Exception:
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                self.root.geometry(f"{sw}x{sh}+0+0")

    def set_loaded_file(self, file_path):
        """Prepara el archivo cargado y activa el botón de iniciar."""
        self.selected_file_path = file_path
        file_name = os.path.basename(file_path)

        self.drop_frame.config(highlightbackground=DARK_RUGRATS["chuckie_yellow"])
        self.drop_label_text.config(
            text=f"📄 Archivo cargado:\n{file_name}\n\n(Haz clic o arrastra otro si deseas cambiarlo)",
            fg=DARK_RUGRATS["chuckie_yellow"]
        )

        self.btn_start.config(
            state=tk.NORMAL,
            bg=DARK_RUGRATS["chuckie_orange"],
            fg="white",
            cursor="hand2"
        )
        self.lbl_status.config(
            text=f"✓ '{file_name}' listo. Pulsa 'INICIAR TRADUCCIÓN BILINGÜE' cuando quieras procesarlo.",
            fg=DARK_RUGRATS["reptar_green"],
            font=("Helvetica", 10, "bold")
        )

    def on_file_dropped(self, event):
        if self.is_processing:
            return
        raw_path = event.data.strip()
        if raw_path.startswith('{') and raw_path.endswith('}'):
            raw_path = raw_path[1:-1]
        if os.path.isfile(raw_path):
            self.set_loaded_file(raw_path)

    def select_file(self):
        if self.is_processing:
            return
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de apuntes",
            filetypes=[("Documentos soportados", "*.pdf *.docx *.odt *.txt *.md")]
        )
        if file_path:
            self.set_loaded_file(file_path)

    # ------------------------------------------------------------------
    # Verificación de cuentas (botón manual, independiente de traducir)
    # ------------------------------------------------------------------
    def verify_accounts_manual(self):
        if self.is_processing or self.is_verifying:
            return

        client_pool = build_client_pool(self.config)
        if not client_pool:
            messagebox.showwarning(
                "Sin cuentas configuradas",
                "No tienes ninguna cuenta con API Key configurada. Pulsa en '⚙ Gestionar APIs'."
            )
            return

        self.is_verifying = True
        self.btn_verify.config(state=tk.DISABLED, cursor="arrow")
        self.lbl_status.config(text="Verificando cuentas...", fg=DARK_RUGRATS["text_muted"])

        threading.Thread(target=self._verify_accounts_worker, args=(client_pool,), daemon=True).start()

    def _verify_accounts_worker(self, client_pool):
        results = check_client_pool(client_pool, status_callback=self.update_status)

        ok_names = [n for n, (ok, _) in results.items() if ok]

        summary_lines = []
        for name, (ok, msg) in results.items():
            icon = "✔" if ok else "✘"
            summary_lines.append(f"{icon} {name}: {msg}")
        summary = "\n".join(summary_lines)

        if ok_names:
            self.update_status(f"Verificación completa: {len(ok_names)}/{len(results)} cuentas funcionando.")
        else:
            self.update_status("Verificación completa: ninguna cuenta funciona ahora mismo.")

        messagebox.showinfo("Resultado de la verificación", summary)

        self.is_verifying = False
        self.btn_verify.config(state=tk.NORMAL, cursor="hand2")

    # ------------------------------------------------------------------
    # Traducción
    # ------------------------------------------------------------------
    def on_start_clicked(self):
        if not self.selected_file_path:
            return

        client_pool = build_client_pool(self.config)
        if not client_pool:
            messagebox.showwarning(
                "API Key requerida",
                "No tienes ninguna cuenta con API Key configurada. Pulsa en '⚙ Gestionar APIs'."
            )
            self.open_api_manager()
            return

        self.is_processing = True
        self.btn_start.config(state=tk.DISABLED, bg="#2e3458", fg=DARK_RUGRATS["text_muted"], cursor="arrow")
        self.btn_verify.config(state=tk.DISABLED, cursor="arrow")
        self.drop_frame.config(cursor="watch")
        self.progress.pack(fill=tk.X, pady=6)
        self.progress.start(10)

        threading.Thread(target=self._process_worker, args=(self.selected_file_path, client_pool), daemon=True).start()

    def on_change_active_profile(self, event=None):
        self.config["active_profile"] = self.active_prof_var.get()
        save_config(self.config)

    def open_api_manager(self):
        ApiManagerDialog(self.root, self.config, self.on_config_updated)

    def on_config_updated(self):
        self.config = load_config()
        self.active_prof_var.set(self.config["active_profile"])
        self.cb_active_prof["values"] = list(self.config["profiles"].keys())

    def _process_worker(self, file_path, client_pool):
        translated_blocks = []
        output_html = os.path.splitext(file_path)[0] + "_Bilingue.html"
        dead_keys = set()
        total_blocks = 0
        interrupted = False

        try:
            # --- Paso 0/3: comprobar de antemano qué cuentas funcionan ---
            self.update_status(f"0/3 Verificando {len(client_pool)} cuenta(s) configurada(s)...")
            check_results = check_client_pool(client_pool, status_callback=self.update_status)
            for name, (ok, _msg) in check_results.items():
                if not ok:
                    dead_keys.add(name)

            working_count = len(client_pool) - len(dead_keys)
            if working_count <= 0:
                raise RuntimeError(
                    "Ninguna de las cuentas/API keys configuradas funciona ahora mismo. "
                    "Revisa '⚙ Gestionar APIs' o pulsa '🔎 Verificar cuentas' para ver el detalle."
                )
            self.update_status(f"0/3 Listo: {working_count}/{len(client_pool)} cuenta(s) disponibles. Empezando...")

            # --- Paso 1/3: extraer el documento ---
            self.update_status("1/3 Extrayendo estructura del documento...")
            blocks = extract_text_from_file(file_path)
            if not blocks:
                raise ValueError("No se pudo extraer texto del archivo.")
            total_blocks = len(blocks)

            # --- Paso 2/3: traducir, rotando cuentas si hace falta ---
            self.update_status(f"2/3 Traduciendo con IA ({total_blocks} secciones)...")
            BATCH_SIZE = 12

            for i in range(0, total_blocks, BATCH_SIZE):
                if len(dead_keys) >= len(client_pool):
                    interrupted = True
                    self.update_status("⚠ Se agotaron todas las cuentas API disponibles. Guardando lo traducido hasta ahora...")
                    break

                batch = blocks[i:i + BATCH_SIZE]
                self.update_status(f"2/3 Traduciendo con IA ({min(i + BATCH_SIZE, total_blocks)}/{total_blocks} secciones)...")

                try:
                    res = translate_blocks_batch(
                        client_pool, batch,
                        status_callback=self.update_status,
                        dead_keys=dead_keys
                    )
                    translated_blocks.extend(res)
                except RuntimeError as e:
                    interrupted = True
                    self.update_status(f"⚠ {e}")
                    break

            # --- Paso 3/3: generar el lector, con lo que se haya conseguido ---
            self.update_status("3/3 Generando lector interactivo...")
            generate_html_viewer(translated_blocks, output_html)

            if interrupted and translated_blocks:
                webbrowser.open(f"file://{os.path.abspath(output_html)}")
                self.update_status(
                    f"⚠ Traducción incompleta: {len(translated_blocks)} bloques traducidos de {total_blocks}. "
                    "Se abrió un lector parcial con lo conseguido."
                )
                messagebox.showwarning(
                    "Traducción incompleta",
                    "Se agotaron todas las cuentas/API keys configuradas antes de terminar.\n\n"
                    f"Se tradujeron {len(translated_blocks)} de {total_blocks} bloques.\n"
                    f"Se generó un lector parcial en:\n{output_html}\n\n"
                    "Añade más cuentas en '⚙ Gestionar APIs' o espera a que se renueve la cuota "
                    "para poder completar el resto."
                )
            elif interrupted:
                self.update_status("Error: ninguna cuenta configurada pudo traducir el documento.")
                messagebox.showerror(
                    "Error en el proceso",
                    "Ninguna de las cuentas/API keys configuradas pudo traducir el documento."
                )
            else:
                self.update_status("¡Completado! Abriendo en el navegador...")
                webbrowser.open(f"file://{os.path.abspath(output_html)}")

        except Exception as e:
            # Fallo inesperado (extracción del archivo, permisos, ninguna cuenta
            # disponible desde el principio, etc.): si algo llegó a traducirse,
            # se intenta salvar igualmente.
            if translated_blocks:
                try:
                    generate_html_viewer(translated_blocks, output_html)
                    webbrowser.open(f"file://{os.path.abspath(output_html)}")
                except Exception:
                    pass
            messagebox.showerror("Error en el proceso", str(e))
            self.update_status("Error al procesar.")

        finally:
            self.is_processing = False
            self.progress.stop()
            self.progress.pack_forget()
            self.drop_frame.config(cursor="hand2")
            self.btn_verify.config(state=tk.NORMAL, cursor="hand2")
            if self.selected_file_path:
                self.btn_start.config(state=tk.NORMAL, bg=DARK_RUGRATS["chuckie_orange"], fg="white", cursor="hand2")

    def update_status(self, text):
        self.lbl_status.config(text=text)
        self.root.update_idletasks()