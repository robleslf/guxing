import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from config import TEMPLATES, save_config, build_client_pool
from core.translator import check_client_pool
from ui.theme import DARK_RUGRATS


class ApiManagerDialog(tk.Toplevel):
    def __init__(self, parent, config, on_save_callback):
        super().__init__(parent)
        self.title("⚙ Gestor de Cuentas y APIs")
        self.geometry("640x620")
        self.minsize(540, 520)
        self.configure(bg=DARK_RUGRATS["bg_dark"])
        self.config = config
        self.on_save_callback = on_save_callback
        self.current_loaded_profile = self.config["active_profile"]
        self.is_verifying = False

        frame = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"], padx=26, pady=24)
        frame.pack(fill=tk.BOTH, expand=True)

        top_bar = tk.Frame(frame, bg=DARK_RUGRATS["bg_dark"])
        top_bar.pack(fill=tk.X, pady=(0, 16))
        tk.Label(top_bar, text="Seleccionar perfil:", font=("Helvetica", 11, "bold"),
                  bg=DARK_RUGRATS["bg_dark"], fg=DARK_RUGRATS["text_light"]).pack(side=tk.LEFT, padx=(0, 8))
        self.selected_profile_var = tk.StringVar(value=self.config["active_profile"])
        self.cb_profiles = ttk.Combobox(top_bar, textvariable=self.selected_profile_var,
                                         values=list(self.config["profiles"].keys()), state="readonly", width=26)
        self.cb_profiles.pack(side=tk.LEFT, padx=(0, 8))
        self.cb_profiles.bind("<<ComboboxSelected>>", self.on_profile_selected)
        tk.Button(top_bar, text="➕ Nuevo", bg=DARK_RUGRATS["tommy_blue"], fg="white", relief="flat",
                  font=("Helvetica", 9, "bold"), padx=8, command=self.add_new_profile).pack(side=tk.LEFT, padx=4)
        tk.Button(top_bar, text="🗑 Borrar", bg=DARK_RUGRATS["chuckie_orange"], fg="white", relief="flat",
                  font=("Helvetica", 9, "bold"), padx=8, command=self.delete_profile).pack(side=tk.LEFT, padx=4)

        fields_frame = tk.LabelFrame(frame, text=" Editar Datos del Perfil ", font=("Helvetica", 10, "bold"),
                                      bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], padx=14, pady=14)
        fields_frame.pack(fill=tk.BOTH, expand=False, pady=10)

        tk.Label(fields_frame, text="Nombre de la cuenta:", bg=DARK_RUGRATS["panel_dark"],
                 fg=DARK_RUGRATS["chuckie_yellow"], font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=8)
        self.entry_name = ttk.Entry(fields_frame, font=("Helvetica", 10))
        self.entry_name.grid(row=0, column=1, sticky=tk.EW, pady=8)

        tk.Label(fields_frame, text="Plantilla rápida:", bg=DARK_RUGRATS["panel_dark"],
                 fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=1, column=0, sticky=tk.W, pady=8)
        self.template_var = tk.StringVar(value="Google Gemini (100% Gratis)")
        self.cb_templates = ttk.Combobox(fields_frame, textvariable=self.template_var,
                                          values=list(TEMPLATES.keys()), state="readonly")
        self.cb_templates.grid(row=1, column=1, sticky=tk.EW, pady=8)
        self.cb_templates.bind("<<ComboboxSelected>>", self.apply_template)

        tk.Label(fields_frame, text="API Key:", bg=DARK_RUGRATS["panel_dark"],
                 fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=2, column=0, sticky=tk.W, pady=8)
        self.entry_key = ttk.Entry(fields_frame, show="*")
        self.entry_key.grid(row=2, column=1, sticky=tk.EW, pady=8)

        tk.Label(fields_frame, text="Base URL:", bg=DARK_RUGRATS["panel_dark"],
                 fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=3, column=0, sticky=tk.W, pady=8)
        self.entry_url = ttk.Entry(fields_frame)
        self.entry_url.grid(row=3, column=1, sticky=tk.EW, pady=8)

        tk.Label(fields_frame, text="Modelo:", bg=DARK_RUGRATS["panel_dark"],
                 fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=4, column=0, sticky=tk.W, pady=8)
        self.entry_model = ttk.Entry(fields_frame)
        self.entry_model.grid(row=4, column=1, sticky=tk.EW, pady=8)

        fields_frame.columnconfigure(1, weight=1)

        btn_frame = tk.Frame(frame, bg=DARK_RUGRATS["bg_dark"])
        btn_frame.pack(fill=tk.X, pady=(16, 0))
        tk.Button(btn_frame, text="💾 Guardar Cambios", bg=DARK_RUGRATS["angelica_purple"], fg="white",
                  font=("Helvetica", 10, "bold"), relief="flat", padx=14, pady=6,
                  command=self.save_profile).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(btn_frame, text="Cerrar", bg="#4a4e69", fg="white", font=("Helvetica", 10), relief="flat",
                  padx=14, pady=6, command=self.destroy).pack(side=tk.LEFT)

        # --- Verificación de cuentas ---
        verify_frame = tk.LabelFrame(frame, text=" Comprobar cuentas configuradas ", font=("Helvetica", 10, "bold"),
                                      bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], padx=14, pady=10)
        verify_frame.pack(fill=tk.BOTH, expand=True, pady=(16, 0))

        verify_top = tk.Frame(verify_frame, bg=DARK_RUGRATS["panel_dark"])
        verify_top.pack(fill=tk.X)
        self.btn_verify = tk.Button(
            verify_top, text="🔎 Verificar todas las cuentas", bg=DARK_RUGRATS["tommy_blue"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=10, pady=6,
            command=self.verify_all_accounts
        )
        self.btn_verify.pack(side=tk.LEFT)
        tk.Label(verify_top, text="(hace una petición mínima a cada cuenta; el gasto es insignificante)",
                 bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_muted"],
                 font=("Helvetica", 9)).pack(side=tk.LEFT, padx=10)

        self.txt_verify_results = tk.Text(
            verify_frame, height=8, bg="#0b0c14", fg=DARK_RUGRATS["text_light"],
            font=("Consolas", 9), relief="flat", wrap="word", state=tk.DISABLED
        )
        self.txt_verify_results.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.on_profile_selected()

    # ------------------------------------------------------------------
    # Verificación de cuentas
    # ------------------------------------------------------------------
    def _append_verify_line(self, text):
        self.txt_verify_results.config(state=tk.NORMAL)
        self.txt_verify_results.insert(tk.END, text + "\n")
        self.txt_verify_results.see(tk.END)
        self.txt_verify_results.config(state=tk.DISABLED)

    def verify_all_accounts(self):
        if self.is_verifying:
            return

        client_pool = build_client_pool(self.config)
        if not client_pool:
            messagebox.showwarning("Sin cuentas", "No hay ninguna cuenta con API Key rellenada todavía.")
            return

        self.is_verifying = True
        self.btn_verify.config(state=tk.DISABLED, cursor="arrow")
        self.txt_verify_results.config(state=tk.NORMAL)
        self.txt_verify_results.delete("1.0", tk.END)
        self.txt_verify_results.config(state=tk.DISABLED)
        self._append_verify_line(f"Comprobando {len(client_pool)} cuenta(s)...")

        import threading
        threading.Thread(target=self._verify_worker, args=(client_pool,), daemon=True).start()

    def _verify_worker(self, client_pool):
        def on_progress(msg):
            # check_client_pool llama a esto desde el hilo de fondo; marshaling
            # a través de 'after' para tocar el widget de forma segura.
            self.after(0, self._append_verify_line, msg)

        results = check_client_pool(client_pool, status_callback=on_progress)

        ok_count = sum(1 for ok, _ in results.values() if ok)

        def finish():
            self._append_verify_line(f"\nResultado: {ok_count}/{len(results)} cuenta(s) funcionando ahora mismo.")
            self.is_verifying = False
            self.btn_verify.config(state=tk.NORMAL, cursor="hand2")

        self.after(0, finish)

    # ------------------------------------------------------------------
    # Gestión de perfiles (sin cambios funcionales)
    # ------------------------------------------------------------------
    def on_profile_selected(self, event=None):
        prof = self.selected_profile_var.get()
        self.current_loaded_profile = prof
        data = self.config["profiles"].get(prof, {})

        self.entry_name.delete(0, tk.END)
        self.entry_name.insert(0, prof)
        self.entry_key.delete(0, tk.END)
        self.entry_key.insert(0, data.get("api_key", ""))
        self.entry_url.delete(0, tk.END)
        self.entry_url.insert(0, data.get("base_url", ""))
        self.entry_model.delete(0, tk.END)
        self.entry_model.insert(0, data.get("model", ""))

    def apply_template(self, event=None):
        tpl = TEMPLATES.get(self.template_var.get(), {})
        if tpl.get("base_url"):
            self.entry_url.delete(0, tk.END)
            self.entry_url.insert(0, tpl["base_url"])
        if tpl.get("model"):
            self.entry_model.delete(0, tk.END)
            self.entry_model.insert(0, tpl["model"])

    def add_new_profile(self):
        name = simpledialog.askstring(
            "Nuevo Perfil",
            "Nombre de la nueva cuenta/perfil:\n(Ej: Gemini Novia, Gemini Felipe...)"
        )
        if name and name.strip():
            name = name.strip()
            if name in self.config["profiles"]:
                messagebox.showwarning("Aviso", "Ya existe un perfil con ese nombre.")
                return
            self.config["profiles"][name] = {
                "api_key": "",
                "base_url": TEMPLATES["Google Gemini (100% Gratis)"]["base_url"],
                "model": TEMPLATES["Google Gemini (100% Gratis)"]["model"]
            }
            self.cb_profiles["values"] = list(self.config["profiles"].keys())
            self.selected_profile_var.set(name)
            self.on_profile_selected()

    def delete_profile(self):
        prof = self.selected_profile_var.get()
        if len(self.config["profiles"]) <= 1:
            messagebox.showwarning("Aviso", "Debes tener al menos un perfil.")
            return
        if messagebox.askyesno("Confirmar", f"¿Seguro que quieres borrar '{prof}'?"):
            del self.config["profiles"][prof]
            new_active = list(self.config["profiles"].keys())[0]
            self.config["active_profile"] = new_active
            self.cb_profiles["values"] = list(self.config["profiles"].keys())
            self.selected_profile_var.set(new_active)
            self.on_profile_selected()
            save_config(self.config)
            self.on_save_callback()

    def save_profile(self):
        old_name = self.current_loaded_profile
        new_name = self.entry_name.get().strip()

        if not new_name:
            messagebox.showwarning("Aviso", "El nombre no puede estar vacío.")
            return

        if new_name != old_name:
            if new_name in self.config["profiles"]:
                messagebox.showwarning("Aviso", f"Ya existe '{new_name}'.")
                return
            del self.config["profiles"][old_name]
            if self.config.get("active_profile") == old_name:
                self.config["active_profile"] = new_name

        self.config["profiles"][new_name] = {
            "api_key": self.entry_key.get().strip(),
            "base_url": self.entry_url.get().strip(),
            "model": self.entry_model.get().strip()
        }
        self.config["active_profile"] = new_name
        self.current_loaded_profile = new_name

        save_config(self.config)
        self.cb_profiles["values"] = list(self.config["profiles"].keys())
        self.selected_profile_var.set(new_name)
        self.on_save_callback()
        messagebox.showinfo("Guardado", f"Perfil '{new_name}' guardado correctamente.")