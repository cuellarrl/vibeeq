#!/usr/bin/env python3
import os
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# --- CONFIGURACIÓN ---
APP_NAME = "VibeEQ Manager"
VERSION = "1.0.0"
# Detecta dónde está instalada la app para poder actualizarse
REPO_DIR = os.path.dirname(os.path.abspath(__file__)) 
EE_PRESETS_DIR = os.path.expanduser("~/.config/easyeffects/output")

class VibeEQApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{VERSION}")
        self.root.geometry("400x600")
        self.root.configure(bg="#1e1e1e")

        # Estilos visuales
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", background="#333", foreground="white", borderwidth=0)
        style.map("TButton", background=[('active', '#1DB954')]) 

        # Título
        tk.Label(root, text="VIBE EQ", font=("Arial", 20, "bold"), bg="#1e1e1e", fg="#1DB954").pack(pady=20)

        # --- BOTONES ---
        btn_frame = tk.Frame(root, bg="#1e1e1e")
        btn_frame.pack(fill="x", padx=20)

        self.btn_import = tk.Button(btn_frame, text="📂 Importar JSON de Poweramp", 
                                    command=self.importar_json, 
                                    bg="#444", fg="white", font=("Arial", 11), relief="flat", padx=10, pady=8)
        self.btn_import.pack(fill="x", pady=5)

        self.btn_update = tk.Button(btn_frame, text="☁️ Buscar Actualizaciones", 
                                    command=self.actualizar_app, 
                                    bg="#222", fg="#aaa", font=("Arial", 9), relief="flat")
        self.btn_update.pack(fill="x", pady=5)

        # --- LISTA ---
        tk.Label(root, text="Tus Presets:", bg="#1e1e1e", fg="white", font=("Arial", 12)).pack(pady=(20,5))
        
        self.list_frame = tk.Frame(root, bg="#121212")
        self.list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        scrollbar = tk.Scrollbar(self.list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.preset_listbox = tk.Listbox(self.list_frame, bg="#252525", fg="white", 
                                         font=("Arial", 11), bd=0, 
                                         yscrollcommand=scrollbar.set, selectbackground="#1DB954")
        self.preset_listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.preset_listbox.yview)
        
        self.preset_listbox.bind('<Double-1>', self.activar_preset)
        self.cargar_lista()

    def cargar_lista(self):
        self.preset_listbox.delete(0, tk.END)
        try:
            Path(EE_PRESETS_DIR).mkdir(parents=True, exist_ok=True)
            archivos = [f.stem for f in Path(EE_PRESETS_DIR).glob("*.json")]
            for arch in sorted(archivos):
                self.preset_listbox.insert(tk.END, arch)
        except Exception:
            pass

    def activar_preset(self, event=None):
        seleccion = self.preset_listbox.curselection()
        if not seleccion: return
        nombre = self.preset_listbox.get(seleccion[0])
        subprocess.run(["easyeffects", "-l", nombre])
        messagebox.showinfo("Vibe", f"Activado: {nombre}")

    def importar_json(self):
        archivo = filedialog.askopenfilename(filetypes=[("JSON", "*.json"), ("Todos", "*.*")])
        if not archivo: return

        try:
            with open(archivo, 'r') as f: data = json.load(f)
            nombre = Path(archivo).stem.replace(" ", "_")
            
            # --- CONVERSIÓN ---
            ee_data = {
                "output": {
                    "blocklist": [], "plugins_order": ["equalizer"],
                    "equalizer": { "left": {}, "right": {}, "num-bands": 0 }
                }
            }
            # Busca bandas en 'preset->bands' o directamente en 'bands'
            bandas = data.get("preset", {}).get("bands", []) or data.get("bands", [])
            
            if not bandas: raise ValueError("No encontré bandas de EQ.")

            for i, b in enumerate(bandas):
                k = f"band{i}"
                info = { "type": "Bell", "mode": "RLC (BT)", "mute": False,
                    "frequency": b.get("frequency", 100),
                    "gain": b.get("gain", 0.0), "q": b.get("q", 1.0) }
                ee_data["output"]["equalizer"]["left"][k] = info
                ee_data["output"]["equalizer"]["right"][k] = info
            
            ee_data["output"]["equalizer"]["num-bands"] = len(bandas)
            
            with open(os.path.join(EE_PRESETS_DIR, f"{nombre}.json"), 'w') as f:
                json.dump(ee_data, f, indent=4)
            
            messagebox.showinfo("Listo", "Preset importado.")
            self.cargar_lista()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def actualizar_app(self):
        try:
            res = subprocess.run(["git", "pull"], cwd=REPO_DIR, capture_output=True, text=True)
            if "Already up to date" in res.stdout:
                messagebox.showinfo("Update", "Ya tienes la última versión.")
            else:
                messagebox.showinfo("Update", "Actualización completada. Reinicia la app.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo conectar a GitHub: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = VibeEQApp(root)
    root.mainloop()
