import os
import time
import shutil
import zipfile
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog

from config import (
    load_config, save_config, build_client_pool,
    load_library, save_library, LIBRARY_BASE_DIR,
    open_folder_in_file_manager, get_topic_folder, TEMPLATES
)
from core.parser import extract_text_from_file
from core.translator import translate_blocks_batch, check_client_pool
from core.viewer_html import generate_html_viewer
from ui.theme import (
    DARK_RUGRATS, IMG_LETRAS_PATH, IMG_ICO_PATH,
    IMG_BTN_LIBROS, IMG_BTN_TRADUCCION, IMG_BTN_APIKEY, IMG_BTN_EXIT,
    apply_rugrats_theme
)

try:
    from tkinterdnd2 import DND_FILES
    HAS_DND = True
except ImportError:
    HAS_DND = False


def load_resized_image(path, target_height=190):
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


def load_button_icon(path, target_size=(26, 26)):
    """Carga y redimensiona un icono para los botones del menú."""
    if not os.path.exists(path):
        return None
    try:
        from PIL import Image, ImageTk
        img = Image.open(path)
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        try:
            return tk.PhotoImage(file=path)
        except Exception:
            return None


class TranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GUXING - Plataforma de Estudio Bilingüe")
        self.root.configure(bg=DARK_RUGRATS["bg_dark"])

        if os.path.exists(IMG_ICO_PATH):
            try:
                self.app_icon = tk.PhotoImage(file=IMG_ICO_PATH)
                self.root.iconphoto(True, self.app_icon)
            except Exception:
                pass

        apply_rugrats_theme(self.root)
        self.maximize_window()
        self.config = load_config()
        self.library = load_library()

        self.container = tk.Frame(self.root, bg=DARK_RUGRATS["bg_dark"])
        self.container.pack(fill=tk.BOTH, expand=True)

        self.scenes = {}
        self.init_scenes()
        self.show_scene("MainMenuScene")

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

    def show_scene(self, scene_name: str):
        for scene in self.scenes.values():
            scene.pack_forget()
        frame = self.scenes[scene_name]
        frame.pack(fill=tk.BOTH, expand=True)
        if hasattr(frame, "on_show"):
            frame.on_show()

    def init_scenes(self):
        self.scenes["MainMenuScene"] = MainMenuScene(self.container, self)
        self.scenes["TranslateScene"] = TranslateScene(self.container, self)
        self.scenes["StudyScene"] = StudyScene(self.container, self)
        self.scenes["ApiScene"] = ApiScene(self.container, self)

    def exit_gracefully(self):
        if messagebox.askyesno("Salir de Guxing", "¿Deseas cerrar la plataforma de estudio?"):
            self.root.destroy()


# ====================================================================
# ESCENA 1: MENÚ PRINCIPAL (CON NUEVOS BOTONES/ICONOS PNG)
# ====================================================================
class MainMenuScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=DARK_RUGRATS["bg_dark"])
        self.app = app

        center_box = tk.Frame(
            self, bg=DARK_RUGRATS["panel_dark"], bd=2, relief="ridge",
            highlightthickness=2, highlightbackground=DARK_RUGRATS["border_comic"],
            padx=45, pady=32
        )
        center_box.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        if os.path.exists(IMG_LETRAS_PATH):
            try:
                self.logo_img = load_resized_image(IMG_LETRAS_PATH, target_height=190)
                tk.Label(center_box, image=self.logo_img, bg=DARK_RUGRATS["panel_dark"]).pack(pady=(0, 10))
            except Exception:
                tk.Label(center_box, text="GUXING", font=("Helvetica", 36, "bold"),
                         fg=DARK_RUGRATS["tommy_blue"], bg=DARK_RUGRATS["panel_dark"]).pack(pady=(0, 10))
        else:
            tk.Label(center_box, text="GUXING", font=("Helvetica", 36, "bold"),
                     fg=DARK_RUGRATS["tommy_blue"], bg=DARK_RUGRATS["panel_dark"]).pack(pady=(0, 10))

        tk.Label(
            center_box,
            text="Plataforma Centralizada de Estudio y Traducción Técnica (Español / Galego ➔ 中文)",
            font=("Helvetica", 11, "bold"),
            fg=DARK_RUGRATS["chuckie_yellow"],
            bg=DARK_RUGRATS["panel_dark"]
        ).pack(pady=(0, 26))

        self.icon_libros = load_button_icon(IMG_BTN_LIBROS, (28, 28))
        self.icon_traduccion = load_button_icon(IMG_BTN_TRADUCCION, (28, 28))
        self.icon_apikey = load_button_icon(IMG_BTN_APIKEY, (28, 28))
        self.icon_exit = load_button_icon(IMG_BTN_EXIT, (24, 24))

        buttons_container = tk.Frame(center_box, bg=DARK_RUGRATS["panel_dark"])
        buttons_container.pack(fill=tk.X)

        btn_font = ("Helvetica", 12, "bold")

        self.btn_study = tk.Button(
            buttons_container,
            text="   Zona de Estudio (Mis Cursos y Apuntes)",
            image=self.icon_libros,
            compound=tk.LEFT if self.icon_libros else tk.NONE,
            bg=DARK_RUGRATS["reptar_green"], fg="#0d1117",
            activebackground=DARK_RUGRATS["reptar_green_hover"],
            font=btn_font, relief="flat", pady=10, padx=16, cursor="hand2", anchor="w",
            command=lambda: self.app.show_scene("StudyScene")
        )
        self.btn_study.pack(fill=tk.X, pady=6)

        self.btn_translate = tk.Button(
            buttons_container,
            text="   Traducir Nuevos Apuntes",
            image=self.icon_traduccion,
            compound=tk.LEFT if self.icon_traduccion else tk.NONE,
            bg=DARK_RUGRATS["chuckie_orange"], fg="white",
            activebackground=DARK_RUGRATS["chuckie_orange_hover"],
            font=btn_font, relief="flat", pady=10, padx=16, cursor="hand2", anchor="w",
            command=lambda: self.app.show_scene("TranslateScene")
        )
        self.btn_translate.pack(fill=tk.X, pady=6)

        self.btn_api = tk.Button(
            buttons_container,
            text="   Gestión de APIs y Verificación",
            image=self.icon_apikey,
            compound=tk.LEFT if self.icon_apikey else tk.NONE,
            bg=DARK_RUGRATS["angelica_purple"], fg="white",
            activebackground=DARK_RUGRATS["angelica_purple_hover"],
            font=btn_font, relief="flat", pady=10, padx=16, cursor="hand2", anchor="w",
            command=lambda: self.app.show_scene("ApiScene")
        )
        self.btn_api.pack(fill=tk.X, pady=6)

        self.btn_exit = tk.Button(
            buttons_container,
            text="   Salir de Guxing",
            image=self.icon_exit,
            compound=tk.LEFT if self.icon_exit else tk.NONE,
            bg=DARK_RUGRATS["border_comic"], fg=DARK_RUGRATS["text_light"],
            activebackground="#3d4573",
            font=("Helvetica", 11, "bold"), relief="flat", pady=8, padx=16, cursor="hand2", anchor="w",
            command=self.app.exit_gracefully
        )
        self.btn_exit.pack(fill=tk.X, pady=(14, 0))


# ====================================================================
# ESCENA 2: ZONA DE ESTUDIO (RENOMBRAR, MOVER, EXPORTAR/IMPORTAR)
# ====================================================================
class StudyScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=DARK_RUGRATS["bg_dark"], padx=26, pady=18)
        self.app = app
        self.selected_topic_ref = None

        top_bar = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"])
        top_bar.pack(fill=tk.X, pady=(0, 14))

        tk.Button(
            top_bar, text="⬅ Volver al Menú", bg=DARK_RUGRATS["border_comic"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2",
            command=lambda: self.app.show_scene("MainMenuScene")
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar, text="📚 Zona de Estudio y Repaso",
            font=("Helvetica", 17, "bold"), fg=DARK_RUGRATS["tommy_blue"], bg=DARK_RUGRATS["bg_dark"]
        ).pack(side=tk.LEFT, padx=18)

        tk.Button(
            top_bar, text="📦 Exportar Backup (.zip)", bg=DARK_RUGRATS["angelica_purple"], fg="white",
            font=("Helvetica", 9, "bold"), relief="flat", padx=10, pady=6, cursor="hand2",
            command=self.export_backup_zip
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            top_bar, text="📥 Importar Backup (.zip)", bg=DARK_RUGRATS["border_comic"], fg="white",
            font=("Helvetica", 9, "bold"), relief="flat", padx=10, pady=6, cursor="hand2",
            command=self.import_backup_zip
        ).pack(side=tk.RIGHT, padx=4)

        tk.Button(
            top_bar, text="📂 Abrir Biblioteca en Explorador", bg=DARK_RUGRATS["reptar_green"], fg="#0d1117",
            font=("Helvetica", 9, "bold"), relief="flat", padx=10, pady=6, cursor="hand2",
            command=lambda: open_folder_in_file_manager(LIBRARY_BASE_DIR)
        ).pack(side=tk.RIGHT, padx=4)

        content_frame = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"])
        content_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = tk.LabelFrame(
            content_frame, text=" Organización de Cursos ",
            bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["chuckie_yellow"],
            font=("Helvetica", 10, "bold"), padx=10, pady=10, bd=2, relief="ridge",
            highlightthickness=1, highlightbackground=DARK_RUGRATS["border_comic"]
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        tree_scroll = ttk.Scrollbar(left_panel)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree = ttk.Treeview(left_panel, yscrollcommand=tree_scroll.set, selectmode="browse")
        self.tree.pack(fill=tk.BOTH, expand=True)
        tree_scroll.config(command=self.tree.yview)
        self.tree.heading("#0", text="Árbol Académico", anchor=tk.W)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_selected)

        btn_tree_box = tk.Frame(left_panel, bg=DARK_RUGRATS["panel_dark"])
        btn_tree_box.pack(fill=tk.X, pady=(10, 0))

        tk.Button(btn_tree_box, text="+ Curso", bg=DARK_RUGRATS["tommy_blue"], fg="white", font=("Helvetica", 9, "bold"),
                  relief="flat", padx=7, pady=4, cursor="hand2", command=self.add_course).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_tree_box, text="+ Asignatura", bg=DARK_RUGRATS["angelica_purple"], fg="white", font=("Helvetica", 9, "bold"),
                  relief="flat", padx=7, pady=4, cursor="hand2", command=self.add_subject).pack(side=tk.LEFT, padx=2)
        tk.Button(btn_tree_box, text="+ Tema", bg=DARK_RUGRATS["reptar_green"], fg="#0d1117", font=("Helvetica", 9, "bold"),
                  relief="flat", padx=7, pady=4, cursor="hand2", command=self.add_topic).pack(side=tk.LEFT, padx=2)
        
        tk.Button(btn_tree_box, text="✏️ Renombrar", bg=DARK_RUGRATS["chuckie_yellow"], fg="#0d1117", font=("Helvetica", 9, "bold"),
                  relief="flat", padx=7, pady=4, cursor="hand2", command=self.rename_selected_tree_item).pack(side=tk.LEFT, padx=4)

        tk.Button(btn_tree_box, text="🗑️ Borrar", bg=DARK_RUGRATS["chuckie_orange"], fg="white", font=("Helvetica", 9, "bold"),
                  relief="flat", padx=7, pady=4, cursor="hand2", command=self.delete_selected_tree_item).pack(side=tk.RIGHT, padx=2)

        right_panel = tk.LabelFrame(
            content_frame, text=" Apuntes Bilingües en este Tema ",
            bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["chuckie_yellow"],
            font=("Helvetica", 10, "bold"), padx=14, pady=10, bd=2, relief="ridge",
            highlightthickness=1, highlightbackground=DARK_RUGRATS["border_comic"]
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.lbl_current_topic = tk.Label(
            right_panel, text="Selecciona un Tema en el árbol de la izquierda",
            font=("Helvetica", 11, "bold"), fg=DARK_RUGRATS["tommy_blue"], bg=DARK_RUGRATS["panel_dark"]
        )
        self.lbl_current_topic.pack(anchor=tk.W, pady=(0, 10))

        self.listbox_docs = tk.Listbox(
            right_panel, bg=DARK_RUGRATS["drop_bg"], fg=DARK_RUGRATS["text_light"],
            font=("Helvetica", 11), relief="flat", bd=1, highlightthickness=1,
            highlightbackground=DARK_RUGRATS["border_comic"], selectbackground=DARK_RUGRATS["tommy_blue"]
        )
        self.listbox_docs.pack(fill=tk.BOTH, expand=True)

        doc_btn_box = tk.Frame(right_panel, bg=DARK_RUGRATS["panel_dark"])
        doc_btn_box.pack(fill=tk.X, pady=(12, 0))

        tk.Button(
            doc_btn_box, text="📖 Abrir Visor", bg=DARK_RUGRATS["tommy_blue"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=10, pady=6, cursor="hand2",
            command=self.open_selected_doc
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            doc_btn_box, text="📤 Exportar HTML", bg=DARK_RUGRATS["reptar_green"], fg="#0d1117",
            font=("Helvetica", 9, "bold"), relief="flat", padx=8, pady=6, cursor="hand2",
            command=self.export_selected_doc
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            doc_btn_box, text="📥 Importar HTML", bg=DARK_RUGRATS["angelica_purple"], fg="white",
            font=("Helvetica", 9, "bold"), relief="flat", padx=8, pady=6, cursor="hand2",
            command=self.import_doc_to_current_topic
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            doc_btn_box, text="📂 Ver Carpeta", bg=DARK_RUGRATS["border_comic"], fg="white",
            font=("Helvetica", 9, "bold"), relief="flat", padx=8, pady=6, cursor="hand2",
            command=self.open_in_file_explorer
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            doc_btn_box, text="🔄 Mover", bg=DARK_RUGRATS["chuckie_yellow"], fg="#0d1117",
            font=("Helvetica", 9, "bold"), relief="flat", padx=8, pady=6, cursor="hand2",
            command=self.move_selected_doc
        ).pack(side=tk.LEFT, padx=(0, 6))

        tk.Button(
            doc_btn_box, text="🗑️ Eliminar", bg=DARK_RUGRATS["chuckie_orange"], fg="white",
            font=("Helvetica", 9, "bold"), relief="flat", padx=8, pady=6, cursor="hand2",
            command=self.delete_selected_doc
        ).pack(side=tk.RIGHT)

    def on_show(self):
        self.app.library = load_library()
        self.render_tree()

    def render_tree(self):
        self.tree.delete(*self.tree.get_children())
        for c_idx, course in enumerate(self.app.library.get("courses", [])):
            cid = f"c_{c_idx}"
            c_node = self.tree.insert("", tk.END, iid=cid, text=f"🎓 {course['name']}", open=True)
            for s_idx, subj in enumerate(course.get("subjects", [])):
                sid = f"s_{c_idx}_{s_idx}"
                s_node = self.tree.insert(c_node, tk.END, iid=sid, text=f"📁 {subj['name']}", open=True)
                for t_idx, topic in enumerate(subj.get("topics", [])):
                    tid = f"t_{c_idx}_{s_idx}_{t_idx}"
                    doc_count = len(topic.get("documents", []))
                    self.tree.insert(s_node, tk.END, iid=tid, text=f"📄 {topic['name']} ({doc_count})")

    def on_tree_selected(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        node_id = selected[0]
        self.listbox_docs.delete(0, tk.END)

        if node_id.startswith("t_"):
            parts = [int(p) for p in node_id.split("_")[1:]]
            topic = self.app.library["courses"][parts[0]]["subjects"][parts[1]]["topics"][parts[2]]
            self.selected_topic_ref = (parts[0], parts[1], parts[2])
            self.lbl_current_topic.config(text=f"Tema: {topic['name']}")
            for doc in topic.get("documents", []):
                self.listbox_docs.insert(tk.END, f"  📘 {doc['title']}  ({doc.get('date', '')})")
        else:
            self.selected_topic_ref = None
            self.lbl_current_topic.config(text="Selecciona un Tema para ver sus apuntes.")

    def add_course(self):
        name = simpledialog.askstring("Nuevo Curso", "Nombre del curso académico (Ej: 1º Grao Informática):")
        if name and name.strip():
            self.app.library.setdefault("courses", []).append({"name": name.strip(), "subjects": []})
            save_library(self.app.library)
            self.render_tree()

    def add_subject(self):
        selected = self.tree.selection()
        if not selected or not selected[0].startswith("c_"):
            messagebox.showwarning("Aviso", "Primero selecciona el Curso en el árbol donde añadir la asignatura.")
            return
        c_idx = int(selected[0].split("_")[1])
        name = simpledialog.askstring("Nueva Asignatura", "Nombre de la asignatura (Ej: Bases de Datos):")
        if name and name.strip():
            self.app.library["courses"][c_idx].setdefault("subjects", []).append({"name": name.strip(), "topics": []})
            save_library(self.app.library)
            self.render_tree()

    def add_topic(self):
        selected = self.tree.selection()
        if not selected or not selected[0].startswith("s_"):
            messagebox.showwarning("Aviso", "Primero selecciona la Asignatura en el árbol donde añadir el tema.")
            return
        parts = [int(p) for p in selected[0].split("_")[1:]]
        name = simpledialog.askstring("Nuevo Tema", "Nombre del tema (Ej: Tema 5 - BD Distribuídas):")
        if name and name.strip():
            self.app.library["courses"][parts[0]]["subjects"][parts[1]].setdefault("topics", []).append({
                "name": name.strip(),
                "documents": []
            })
            save_library(self.app.library)
            self.render_tree()

    def rename_selected_tree_item(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Aviso", "Selecciona primero en el árbol qué elemento deseas renombrar.")
            return

        node_id = selected[0]
        parts = [int(p) for p in node_id.split("_")[1:]]

        if node_id.startswith("c_"):
            c_idx = parts[0]
            current_name = self.app.library["courses"][c_idx]["name"]
            new_name = simpledialog.askstring("Renombrar Curso", f"Nuevo nombre para el curso:\n'{current_name}'", initialvalue=current_name)
            if new_name and new_name.strip() and new_name.strip() != current_name:
                self.app.library["courses"][c_idx]["name"] = new_name.strip()
                save_library(self.app.library)
                self.render_tree()

        elif node_id.startswith("s_"):
            c_idx, s_idx = parts[0], parts[1]
            current_name = self.app.library["courses"][c_idx]["subjects"][s_idx]["name"]
            new_name = simpledialog.askstring("Renombrar Asignatura", f"Nuevo nombre para la asignatura:\n'{current_name}'", initialvalue=current_name)
            if new_name and new_name.strip() and new_name.strip() != current_name:
                self.app.library["courses"][c_idx]["subjects"][s_idx]["name"] = new_name.strip()
                save_library(self.app.library)
                self.render_tree()

        elif node_id.startswith("t_"):
            c_idx, s_idx, t_idx = parts[0], parts[1], parts[2]
            current_name = self.app.library["courses"][c_idx]["subjects"][s_idx]["topics"][t_idx]["name"]
            new_name = simpledialog.askstring("Renombrar Tema", f"Nuevo nombre para el tema:\n'{current_name}'", initialvalue=current_name)
            if new_name and new_name.strip() and new_name.strip() != current_name:
                self.app.library["courses"][c_idx]["subjects"][s_idx]["topics"][t_idx]["name"] = new_name.strip()
                save_library(self.app.library)
                self.render_tree()
                self.lbl_current_topic.config(text=f"Tema: {new_name.strip()}")

    def delete_selected_tree_item(self):
        selected = self.tree.selection()
        if not selected:
            return
        node_id = selected[0]
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas eliminar este elemento y todo su contenido?"):
            parts = [int(p) for p in node_id.split("_")[1:]]
            if node_id.startswith("c_"):
                del self.app.library["courses"][parts[0]]
            elif node_id.startswith("s_"):
                del self.app.library["courses"][parts[0]]["subjects"][parts[1]]
            elif node_id.startswith("t_"):
                del self.app.library["courses"][parts[0]]["subjects"][parts[1]]["topics"][parts[2]]
            save_library(self.app.library)
            self.render_tree()
            self.listbox_docs.delete(0, tk.END)

    def open_selected_doc(self):
        if not self.selected_topic_ref:
            return
        sel_idx = self.listbox_docs.curselection()
        if not sel_idx:
            messagebox.showwarning("Aviso", "Selecciona un apunte de la lista.")
            return
        c, s, t = self.selected_topic_ref
        doc = self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]
        path = doc.get("html_path")
        if path and os.path.exists(path):
            webbrowser.open(f"file://{os.path.abspath(path)}")
        else:
            messagebox.showerror("Error", "No se encontró el archivo HTML generado.")

    def export_selected_doc(self):
        if not self.selected_topic_ref:
            messagebox.showwarning("Aviso", "Selecciona primero un tema y un apunte.")
            return
        sel_idx = self.listbox_docs.curselection()
        if not sel_idx:
            messagebox.showwarning("Aviso", "Selecciona el apunte que deseas exportar.")
            return
        
        c, s, t = self.selected_topic_ref
        doc = self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]
        src_path = doc.get("html_path", "")

        if not os.path.exists(src_path):
            messagebox.showerror("Error", "El archivo original no se encuentra en el disco.")
            return

        default_name = os.path.basename(src_path)
        dest_file = filedialog.asksaveasfilename(
            title="Exportar Apunte Bilingüe",
            initialfile=default_name,
            filetypes=[("Documento HTML Bilingüe", "*.html"), ("Todos los archivos", "*.*")]
        )
        if dest_file:
            shutil.copy2(src_path, dest_file)
            messagebox.showinfo("Exportado", f"Apunte exportado con éxito a:\n{dest_file}")

    def import_doc_to_current_topic(self):
        if not self.selected_topic_ref:
            messagebox.showwarning("Aviso", "Selecciona primero el Tema en el árbol donde quieres importar el apunte.")
            return

        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo HTML bilingüe para importar",
            filetypes=[("Archivos HTML", "*.html *.htm"), ("Todos los archivos", "*.*")]
        )
        if not file_path:
            return

        c, s, t = self.selected_topic_ref
        course_name = self.app.library["courses"][c]["name"]
        subject_name = self.app.library["courses"][c]["subjects"][s]["name"]
        topic_name = self.app.library["courses"][c]["subjects"][s]["topics"][t]["name"]

        topic_dir = get_topic_folder(course_name, subject_name, topic_name)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        dest_filename = f"{base_name}_{int(time.time())}.html"
        dest_path = os.path.join(topic_dir, dest_filename)

        shutil.copy2(file_path, dest_path)

        doc_entry = {
            "title": base_name.replace("_Bilingue", ""),
            "html_path": dest_path,
            "date": time.strftime("%Y-%m-%d %H:%M")
        }
        self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"].append(doc_entry)
        save_library(self.app.library)
        self.render_tree()
        self.on_tree_selected(None)
        messagebox.showinfo("Importado", f"Apunte '{doc_entry['title']}' importado correctamente al tema.")

    def export_backup_zip(self):
        dest_zip = filedialog.asksaveasfilename(
            title="Guardar Copia de Seguridad de Guxing",
            initialfile=f"Guxing_Backup_{time.strftime('%Y%m%d')}.zip",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if not dest_zip:
            return

        try:
            with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                library_file = os.path.join(os.path.dirname(LIBRARY_BASE_DIR), "library.json")
                if os.path.exists(library_file):
                    zipf.write(library_file, "library.json")

                for root_dir, _, files in os.walk(LIBRARY_BASE_DIR):
                    for file in files:
                        full_path = os.path.join(root_dir, file)
                        rel_path = os.path.relpath(full_path, os.path.dirname(LIBRARY_BASE_DIR))
                        zipf.write(full_path, rel_path)

            messagebox.showinfo("Backup Creado", f"Copia de seguridad guardada con éxito en:\n{dest_zip}")
        except Exception as e:
            messagebox.showerror("Error en Backup", str(e))

    def import_backup_zip(self):
        zip_path = filedialog.askopenfilename(
            title="Seleccionar Backup ZIP de Guxing",
            filetypes=[("Archivo ZIP", "*.zip")]
        )
        if not zip_path:
            return

        if not messagebox.askyesno("Confirmar Importación", "¿Deseas restaurar e integrar los cursos de este Backup?"):
            return

        try:
            base_app_dir = os.path.dirname(LIBRARY_BASE_DIR)
            with zipfile.ZipFile(zip_path, "r") as zipf:
                zipf.extractall(base_app_dir)

            self.app.library = load_library()
            self.render_tree()
            messagebox.showinfo("Éxito", "Biblioteca restaurada e integrada correctamente.")
        except Exception as e:
            messagebox.showerror("Error al importar backup", str(e))

    def open_in_file_explorer(self):
        if not self.selected_topic_ref:
            open_folder_in_file_manager(LIBRARY_BASE_DIR)
            return
            
        c, s, t = self.selected_topic_ref
        sel_idx = self.listbox_docs.curselection()
        
        if sel_idx:
            doc = self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]
            html_path = doc.get("html_path", "")
            if html_path and os.path.exists(html_path):
                open_folder_in_file_manager(html_path)
                return
        
        course = self.app.library["courses"][c]["name"]
        subj = self.app.library["courses"][c]["subjects"][s]["name"]
        top = self.app.library["courses"][c]["subjects"][s]["topics"][t]["name"]
        folder = get_topic_folder(course, subj, top)
        open_folder_in_file_manager(folder)

    def move_selected_doc(self):
        if not self.selected_topic_ref:
            return
        sel_idx = self.listbox_docs.curselection()
        if not sel_idx:
            messagebox.showwarning("Aviso", "Selecciona el apunte que deseas mover.")
            return

        c, s, t = self.selected_topic_ref
        doc = self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]

        all_topics = []
        for c_i, crs in enumerate(self.app.library.get("courses", [])):
            for s_i, sbj in enumerate(crs.get("subjects", [])):
                for t_i, top in enumerate(sbj.get("topics", [])):
                    if (c_i, s_i, t_i) != (c, s, t):
                        label = f"{crs['name']} ➔ {sbj['name']} ➔ {top['name']}"
                        all_topics.append(((c_i, s_i, t_i), label))

        if not all_topics:
            messagebox.showinfo("Mover", "No hay otros temas disponibles para mover este documento.")
            return

        move_win = tk.Toplevel(self)
        move_win.title("Mover Apunte a otro Tema")
        move_win.geometry("520x340")
        move_win.configure(bg=DARK_RUGRATS["bg_dark"])

        tk.Label(move_win, text=f"Mover '{doc['title']}' a:", bg=DARK_RUGRATS["bg_dark"],
                 fg=DARK_RUGRATS["chuckie_yellow"], font=("Helvetica", 11, "bold")).pack(pady=10)

        lb = tk.Listbox(move_win, font=("Helvetica", 10), bg=DARK_RUGRATS["drop_bg"], fg=DARK_RUGRATS["text_light"],
                        selectbackground=DARK_RUGRATS["tommy_blue"], relief="flat", highlightbackground=DARK_RUGRATS["border_comic"])
        lb.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)
        for _, label in all_topics:
            lb.insert(tk.END, label)
        lb.select_set(0)

        def do_move():
            idx = lb.curselection()
            if not idx:
                return
            target_ref = all_topics[idx[0]][0]
            del self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]
            
            tc, ts, tt = target_ref
            old_path = doc.get("html_path", "")
            target_folder = get_topic_folder(
                self.app.library["courses"][tc]["name"],
                self.app.library["courses"][tc]["subjects"][ts]["name"],
                self.app.library["courses"][tc]["subjects"][ts]["topics"][tt]["name"]
            )
            if old_path and os.path.exists(old_path):
                new_path = os.path.join(target_folder, os.path.basename(old_path))
                shutil.move(old_path, new_path)
                doc["html_path"] = new_path

            self.app.library["courses"][tc]["subjects"][ts]["topics"][tt]["documents"].append(doc)
            save_library(self.app.library)
            move_win.destroy()
            self.render_tree()
            self.on_tree_selected(None)
            messagebox.showinfo("Éxito", "Apunte movido correctamente.")

        tk.Button(move_win, text="Confirmar Movimiento", bg=DARK_RUGRATS["reptar_green"], fg="#0d1117",
                  font=("Helvetica", 10, "bold"), relief="flat", padx=14, pady=6, command=do_move).pack(pady=10)

    def delete_selected_doc(self):
        if not self.selected_topic_ref:
            return
        sel_idx = self.listbox_docs.curselection()
        if not sel_idx:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este apunte de la biblioteca?"):
            c, s, t = self.selected_topic_ref
            doc = self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]
            path = doc.get("html_path", "")
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass
            del self.app.library["courses"][c]["subjects"][s]["topics"][t]["documents"][sel_idx[0]]
            save_library(self.app.library)
            self.render_tree()
            self.on_tree_selected(None)


# ====================================================================
# ESCENA 3: TRADUCIR NUEVOS APUNTES
# ====================================================================
class TranslateScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=DARK_RUGRATS["bg_dark"], padx=26, pady=18)
        self.app = app
        self.selected_file_path = None
        self.is_processing = False

        top_bar = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"])
        top_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            top_bar, text="⬅ Volver al Menú", bg=DARK_RUGRATS["border_comic"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2",
            command=lambda: self.app.show_scene("MainMenuScene")
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar, text="⚡ Traducir y Asignar a mi Estudio",
            font=("Helvetica", 17, "bold"), fg=DARK_RUGRATS["chuckie_orange"], bg=DARK_RUGRATS["bg_dark"]
        ).pack(side=tk.LEFT, padx=18)

        dest_box = tk.LabelFrame(
            self, text=" 🎯 1. ¿Dónde guardarás este apunte en tu zona de estudio? ",
            bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["chuckie_yellow"],
            font=("Helvetica", 10, "bold"), padx=15, pady=10, bd=2, relief="ridge",
            highlightthickness=1, highlightbackground=DARK_RUGRATS["border_comic"]
        )
        dest_box.pack(fill=tk.X, pady=(0, 10))

        grid_frame = tk.Frame(dest_box, bg=DARK_RUGRATS["panel_dark"])
        grid_frame.pack(fill=tk.X)

        tk.Label(grid_frame, text="Curso:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10, "bold")).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.cb_course = ttk.Combobox(grid_frame, state="readonly", width=20)
        self.cb_course.grid(row=0, column=1, padx=5, pady=4)
        self.cb_course.bind("<<ComboboxSelected>>", self.on_course_selected)

        tk.Label(grid_frame, text="Asignatura:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10, "bold")).grid(row=0, column=2, padx=5, sticky=tk.W)
        self.cb_subject = ttk.Combobox(grid_frame, state="readonly", width=20)
        self.cb_subject.grid(row=0, column=3, padx=5, pady=4)
        self.cb_subject.bind("<<ComboboxSelected>>", self.on_subject_selected)

        tk.Label(grid_frame, text="Tema:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10, "bold")).grid(row=0, column=4, padx=5, sticky=tk.W)
        self.cb_topic = ttk.Combobox(grid_frame, state="readonly", width=20)
        self.cb_topic.grid(row=0, column=5, padx=5, pady=4)

        tk.Button(
            grid_frame, text="+ Crear Rápido", bg=DARK_RUGRATS["angelica_purple"], fg="white",
            font=("Helvetica", 9, "bold"), relief="flat", padx=10, pady=3, cursor="hand2", command=self.quick_create_topic
        ).grid(row=0, column=6, padx=10)

        # Drop Zone
        self.drop_frame = tk.Frame(self, bg=DARK_RUGRATS["drop_bg"], bd=3, relief="ridge",
                                   highlightthickness=2, highlightbackground=DARK_RUGRATS["border_comic"])
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=8)

        self.drop_label_text = tk.Label(
            self.drop_frame,
            text="📂 Arrastra aquí tus apuntes (PDF, Word, ODT, TXT)\no haz clic para seleccionar el archivo",
            font=("Helvetica", 13, "bold"), fg=DARK_RUGRATS["text_light"], bg=DARK_RUGRATS["drop_bg"]
        )
        self.drop_label_text.pack(expand=True)

        self.drop_frame.bind("<Button-1>", lambda e: self.select_file())
        self.drop_label_text.bind("<Button-1>", lambda e: self.select_file())

        if HAS_DND:
            self.drop_frame.drop_target_register(DND_FILES)
            self.drop_frame.dnd_bind('<<Drop>>', self.on_file_dropped)

        action_bar = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"])
        action_bar.pack(fill=tk.X, pady=6)

        self.btn_verify = tk.Button(
            action_bar, text="🔍 Comprobar APIs antes de traducir", bg=DARK_RUGRATS["tommy_blue"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=12, pady=8, cursor="hand2", command=self.verify_apis
        )
        self.btn_verify.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_start = tk.Button(
            action_bar, text="🚀 INICIAR TRADUCCIÓN BILINGÜE", font=("Helvetica", 12, "bold"),
            bg=DARK_RUGRATS["border_comic"], fg=DARK_RUGRATS["text_muted"], state=tk.DISABLED, relief="flat", pady=8,
            cursor="arrow", command=self.start_translation
        )
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.progress = ttk.Progressbar(self, mode='indeterminate')
        self.lbl_status = tk.Label(self, text="Selecciona un tema y un archivo para empezar.",
                                   bg=DARK_RUGRATS["bg_dark"], fg=DARK_RUGRATS["text_muted"])
        self.lbl_status.pack(pady=4)

    def on_show(self):
        self.app.library = load_library()
        self.populate_courses()

    def populate_courses(self):
        courses = [c["name"] for c in self.app.library.get("courses", [])]
        self.cb_course["values"] = courses
        if courses:
            self.cb_course.current(0)
            self.on_course_selected()
        else:
            self.cb_course.set("")
            self.cb_subject.set("")
            self.cb_topic.set("")
            self.cb_subject["values"] = []
            self.cb_topic["values"] = []

    def on_course_selected(self, event=None):
        c_idx = self.cb_course.current()
        if c_idx < 0:
            return
        subjects = [s["name"] for s in self.app.library["courses"][c_idx].get("subjects", [])]
        self.cb_subject["values"] = subjects
        if subjects:
            self.cb_subject.current(0)
            self.on_subject_selected()
        else:
            self.cb_subject.set("")
            self.cb_topic.set("")
            self.cb_topic["values"] = []

    def on_subject_selected(self, event=None):
        c_idx = self.cb_course.current()
        s_idx = self.cb_subject.current()
        if c_idx < 0 or s_idx < 0:
            return
        topics = [t["name"] for t in self.app.library["courses"][c_idx]["subjects"][s_idx].get("topics", [])]
        self.cb_topic["values"] = topics
        if topics:
            self.cb_topic.current(0)
        else:
            self.cb_topic.set("")

    def quick_create_topic(self):
        c_name = simpledialog.askstring("Paso 1/3", "Nombre del Curso:")
        if not c_name: return
        s_name = simpledialog.askstring("Paso 2/3", "Nombre de la Asignatura:")
        if not s_name: return
        t_name = simpledialog.askstring("Paso 3/3", "Nombre del Tema:")
        if not t_name: return

        c_match = next((c for c in self.app.library.setdefault("courses", []) if c["name"] == c_name), None)
        if not c_match:
            c_match = {"name": c_name, "subjects": []}
            self.app.library["courses"].append(c_match)

        s_match = next((s for s in c_match["subjects"] if s["name"] == s_name), None)
        if not s_match:
            s_match = {"name": s_name, "topics": []}
            c_match["subjects"].append(s_match)

        s_match["topics"].append({"name": t_name, "documents": []})
        save_library(self.app.library)
        self.populate_courses()
        self.cb_course.set(c_name)
        self.on_course_selected()
        self.cb_subject.set(s_name)
        self.on_subject_selected()
        self.cb_topic.set(t_name)

    def select_file(self):
        if self.is_processing: return
        file_path = filedialog.askopenfilename(
            title="Seleccionar archivo de apuntes",
            filetypes=[("Documentos soportados", "*.pdf *.docx *.odt *.txt *.md")]
        )
        if file_path:
            self.set_loaded_file(file_path)

    def on_file_dropped(self, event):
        if self.is_processing: return
        raw_path = event.data.strip()
        if raw_path.startswith('{') and raw_path.endswith('}'):
            raw_path = raw_path[1:-1]
        if os.path.isfile(raw_path):
            self.set_loaded_file(raw_path)

    def set_loaded_file(self, file_path):
        self.selected_file_path = file_path
        file_name = os.path.basename(file_path)
        self.drop_frame.config(highlightbackground=DARK_RUGRATS["chuckie_yellow"])
        self.drop_label_text.config(
            text=f"✓ Archivo cargado:\n{file_name}\n\n(Haz clic para cambiarlo)",
            fg=DARK_RUGRATS["chuckie_yellow"]
        )
        self.btn_start.config(state=tk.NORMAL, bg=DARK_RUGRATS["chuckie_orange"], fg="white", cursor="hand2")
        self.lbl_status.config(text=f"Listo para procesar '{file_name}'", fg=DARK_RUGRATS["reptar_green"])

    def verify_apis(self):
        pool = build_client_pool(self.app.config)
        if not pool:
            messagebox.showwarning("APIs", "No hay APIs configuradas. Dirígete a 'Gestión de APIs'.")
            return
        self.lbl_status.config(text="Verificando conexión con los proveedores de IA...")
        threading.Thread(target=self._verify_worker, args=(pool,), daemon=True).start()

    def _verify_worker(self, pool):
        res = check_client_pool(pool)
        ok_count = sum(1 for ok, _ in res.values() if ok)
        msg = f"Verificación: {ok_count}/{len(res)} cuenta(s) funcionando correctamente."
        self.update_status(msg)
        self.after(0, lambda: messagebox.showinfo("Estado de APIs", msg))

    def start_translation(self):
        if not self.selected_file_path:
            return
        c_idx = self.cb_course.current()
        s_idx = self.cb_subject.current()
        t_idx = self.cb_topic.current()

        if c_idx < 0 or s_idx < 0 or t_idx < 0 or not self.cb_topic.get():
            messagebox.showwarning("Falta Asignación", "Debes seleccionar un Curso, Asignatura y Tema de destino.")
            return

        client_pool = build_client_pool(self.app.config)
        if not client_pool:
            messagebox.showwarning("API Key requerida", "No hay APIs configuradas. Ve a 'Gestión de APIs'.")
            return

        self.is_processing = True
        self.btn_start.config(state=tk.DISABLED, bg=DARK_RUGRATS["border_comic"], fg=DARK_RUGRATS["text_muted"])
        self.progress.pack(fill=tk.X, pady=6)
        self.progress.start(10)

        threading.Thread(
            target=self._process_worker,
            args=(self.selected_file_path, client_pool, c_idx, s_idx, t_idx),
            daemon=True
        ).start()

    def _process_worker(self, file_path, client_pool, c_idx, s_idx, t_idx):
        try:
            self.update_status("1/3 Extrayendo texto y estructurando secciones...")
            blocks = extract_text_from_file(file_path)
            total_blocks = len(blocks)

            self.update_status(f"2/3 Traduciendo con IA ({total_blocks} secciones)...")
            BATCH_SIZE = 12
            translated_blocks = []
            dead_keys = set()

            for i in range(0, total_blocks, BATCH_SIZE):
                batch = blocks[i:i + BATCH_SIZE]
                self.update_status(f"Traduciendo lote ({min(i+BATCH_SIZE, total_blocks)}/{total_blocks})...")
                res = translate_blocks_batch(
                    client_pool, batch,
                    status_callback=self.update_status,
                    dead_keys=dead_keys
                )
                translated_blocks.extend(res)

            self.update_status("3/3 Guardando en tu biblioteca...")
            course_name = self.app.library["courses"][c_idx]["name"]
            subject_name = self.app.library["courses"][c_idx]["subjects"][s_idx]["name"]
            topic_name = self.app.library["courses"][c_idx]["subjects"][s_idx]["topics"][t_idx]["name"]
            
            topic_dir = get_topic_folder(course_name, subject_name, topic_name)

            base_name = os.path.splitext(os.path.basename(file_path))[0]
            out_filename = f"{base_name}_Bilingue_{int(time.time())}.html"
            dest_html_path = os.path.join(topic_dir, out_filename)

            generate_html_viewer(translated_blocks, dest_html_path)

            doc_entry = {
                "title": base_name,
                "html_path": dest_html_path,
                "date": time.strftime("%Y-%m-%d %H:%M")
            }
            self.app.library["courses"][c_idx]["subjects"][s_idx]["topics"][t_idx]["documents"].append(doc_entry)
            save_library(self.app.library)

            self.update_status("¡Completado con éxito! Abriendo apunte...")
            webbrowser.open(f"file://{os.path.abspath(dest_html_path)}")

        except Exception as e:
            err_msg = str(e)
            self.after(0, lambda: messagebox.showerror("Error en la traducción", err_msg))
            self.update_status("Error durante el procesamiento.")
        finally:
            def _cleanup():
                self.is_processing = False
                self.progress.stop()
                self.progress.pack_forget()
                self.btn_start.config(state=tk.NORMAL, bg=DARK_RUGRATS["chuckie_orange"], fg="white")
            self.after(0, _cleanup)

    def update_status(self, text):
        def _set_text():
            self.lbl_status.config(text=text)
            self.update_idletasks()
        self.after(0, _set_text)


# ====================================================================
# ESCENA 4: GESTIÓN DE APIS Y VERIFICACIÓN
# ====================================================================
class ApiScene(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=DARK_RUGRATS["bg_dark"], padx=26, pady=18)
        self.app = app

        top_bar = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"])
        top_bar.pack(fill=tk.X, pady=(0, 14))

        tk.Button(
            top_bar, text="⬅ Volver al Menú", bg=DARK_RUGRATS["border_comic"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2",
            command=lambda: self.app.show_scene("MainMenuScene")
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar, text="🔑 Configuración de Modelos y APIs",
            font=("Helvetica", 17, "bold"), fg=DARK_RUGRATS["angelica_purple"], bg=DARK_RUGRATS["bg_dark"]
        ).pack(side=tk.LEFT, padx=18)

        prof_bar = tk.Frame(self, bg=DARK_RUGRATS["bg_dark"])
        prof_bar.pack(fill=tk.X, pady=(0, 10))

        tk.Label(prof_bar, text="Perfil Activo:", font=("Helvetica", 11, "bold"),
                 bg=DARK_RUGRATS["bg_dark"], fg=DARK_RUGRATS["text_light"]).pack(side=tk.LEFT, padx=(0, 8))

        self.selected_profile_var = tk.StringVar(value=self.app.config.get("active_profile", ""))
        self.cb_profiles = ttk.Combobox(prof_bar, textvariable=self.selected_profile_var, state="readonly", width=26)
        self.cb_profiles.pack(side=tk.LEFT, padx=(0, 8))
        self.cb_profiles.bind("<<ComboboxSelected>>", self.on_profile_selected)

        tk.Button(prof_bar, text="+ Nuevo Perfil", bg=DARK_RUGRATS["tommy_blue"], fg="white", relief="flat",
                  font=("Helvetica", 9, "bold"), padx=8, cursor="hand2", command=self.add_new_profile).pack(side=tk.LEFT, padx=4)
        tk.Button(prof_bar, text="Borrar Perfil", bg=DARK_RUGRATS["chuckie_orange"], fg="white", relief="flat",
                  font=("Helvetica", 9, "bold"), padx=8, cursor="hand2", command=self.delete_profile).pack(side=tk.LEFT, padx=4)

        fields_frame = tk.LabelFrame(
            self, text=" Datos del Perfil ", font=("Helvetica", 10, "bold"),
            bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["chuckie_yellow"], padx=16, pady=12,
            bd=2, relief="ridge", highlightthickness=1, highlightbackground=DARK_RUGRATS["border_comic"]
        )
        fields_frame.pack(fill=tk.X, pady=10)

        tk.Label(fields_frame, text="Nombre:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=6)
        self.entry_name = ttk.Entry(fields_frame, font=("Helvetica", 10))
        self.entry_name.grid(row=0, column=1, sticky=tk.EW, pady=6)

        tk.Label(fields_frame, text="Plantilla:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=1, column=0, sticky=tk.W, pady=6)
        self.template_var = tk.StringVar(value="Google Gemini (100% Gratis)")
        self.cb_templates = ttk.Combobox(fields_frame, textvariable=self.template_var, values=list(TEMPLATES.keys()), state="readonly")
        self.cb_templates.grid(row=1, column=1, sticky=tk.EW, pady=6)
        self.cb_templates.bind("<<ComboboxSelected>>", self.apply_template)

        tk.Label(fields_frame, text="API Key:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=2, column=0, sticky=tk.W, pady=6)
        self.entry_key = ttk.Entry(fields_frame, show="*")
        self.entry_key.grid(row=2, column=1, sticky=tk.EW, pady=6)

        tk.Label(fields_frame, text="Base URL:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=3, column=0, sticky=tk.W, pady=6)
        self.entry_url = ttk.Entry(fields_frame)
        self.entry_url.grid(row=3, column=1, sticky=tk.EW, pady=6)

        tk.Label(fields_frame, text="Modelo:", bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["text_light"], font=("Helvetica", 10)).grid(row=4, column=0, sticky=tk.W, pady=6)
        self.entry_model = ttk.Entry(fields_frame)
        self.entry_model.grid(row=4, column=1, sticky=tk.EW, pady=6)
        fields_frame.columnconfigure(1, weight=1)

        tk.Button(fields_frame, text="💾 Guardar Cambios del Perfil", bg=DARK_RUGRATS["reptar_green"], fg="#0d1117",
                  font=("Helvetica", 10, "bold"), relief="flat", padx=14, pady=6, cursor="hand2", command=self.save_profile).grid(row=5, column=1, sticky=tk.E, pady=10)

        verify_frame = tk.LabelFrame(
            self, text=" Comprobación y Test de Cuentas ", font=("Helvetica", 10, "bold"),
            bg=DARK_RUGRATS["panel_dark"], fg=DARK_RUGRATS["chuckie_yellow"], padx=14, pady=10,
            bd=2, relief="ridge", highlightthickness=1, highlightbackground=DARK_RUGRATS["border_comic"]
        )
        verify_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        tk.Button(
            verify_frame, text="🔍 Testear todas las cuentas ahora", bg=DARK_RUGRATS["tommy_blue"], fg="white",
            font=("Helvetica", 10, "bold"), relief="flat", padx=12, pady=6, cursor="hand2", command=self.verify_all
        ).pack(anchor=tk.W)

        self.txt_verify = tk.Text(verify_frame, height=7, bg=DARK_RUGRATS["drop_bg"], fg=DARK_RUGRATS["text_light"],
                                  font=("Consolas", 9), relief="flat", wrap="word", state=tk.DISABLED,
                                  highlightbackground=DARK_RUGRATS["border_comic"], bd=1)
        self.txt_verify.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.on_show()

    def on_show(self):
        self.app.config = load_config()
        self.cb_profiles["values"] = list(self.app.config["profiles"].keys())
        active = self.app.config.get("active_profile")
        if active in self.app.config["profiles"]:
            self.selected_profile_var.set(active)
            self.on_profile_selected()

    def on_profile_selected(self, event=None):
        prof = self.selected_profile_var.get()
        data = self.app.config["profiles"].get(prof, {})
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
        name = simpledialog.askstring("Nuevo Perfil", "Nombre de la cuenta (Ej: Gemini Secundaria):")
        if name and name.strip():
            name = name.strip()
            self.app.config["profiles"][name] = {
                "api_key": "",
                "base_url": TEMPLATES["Google Gemini (100% Gratis)"]["base_url"],
                "model": "gemini-1.5-flash"
            }
            save_config(self.app.config)
            self.on_show()
            self.selected_profile_var.set(name)
            self.on_profile_selected()

    def delete_profile(self):
        prof = self.selected_profile_var.get()
        if len(self.app.config["profiles"]) <= 1:
            messagebox.showwarning("Aviso", "Debes tener al menos un perfil configurado.")
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar el perfil '{prof}'?"):
            del self.app.config["profiles"][prof]
            new_active = list(self.app.config["profiles"].keys())[0]
            self.app.config["active_profile"] = new_active
            save_config(self.app.config)
            self.on_show()

    def save_profile(self):
        old_name = self.selected_profile_var.get()
        new_name = self.entry_name.get().strip()
        if not new_name:
            messagebox.showwarning("Aviso", "El nombre no puede estar vacío.")
            return

        if new_name != old_name:
            del self.app.config["profiles"][old_name]
            if self.app.config.get("active_profile") == old_name:
                self.app.config["active_profile"] = new_name

        self.app.config["profiles"][new_name] = {
            "api_key": self.entry_key.get().strip(),
            "base_url": self.entry_url.get().strip(),
            "model": self.entry_model.get().strip()
        }
        self.app.config["active_profile"] = new_name
        save_config(self.app.config)
        self.on_show()
        messagebox.showinfo("Guardado", f"Perfil '{new_name}' actualizado con éxito.")

    def verify_all(self):
        pool = build_client_pool(self.app.config)
        if not pool:
            messagebox.showwarning("Sin Cuentas", "No hay cuentas con API Key para verificar.")
            return
        self.txt_verify.config(state=tk.NORMAL)
        self.txt_verify.delete("1.0", tk.END)
        self.txt_verify.insert(tk.END, "Iniciando comprobación de cuentas...\n")
        self.txt_verify.config(state=tk.DISABLED)

        threading.Thread(target=self._run_verify, args=(pool,), daemon=True).start()

    def _run_verify(self, pool):
        def log(text):
            self.txt_verify.config(state=tk.NORMAL)
            self.txt_verify.insert(tk.END, text + "\n")
            self.txt_verify.see(tk.END)
            self.txt_verify.config(state=tk.DISABLED)

        res = check_client_pool(pool, status_callback=log)
        ok_count = sum(1 for ok, _ in res.values() if ok)
        log(f"\nResultado final: {ok_count}/{len(res)} cuenta(s) listas para usar.")