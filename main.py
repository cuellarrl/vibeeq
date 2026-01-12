#!/usr/bin/env python3
import os
import json
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# --- CONFIGURACIÓN DE LA LEY ---
APP_NAME = "VibeEQ Manager"
VERSION = "4.0.0"
EE_PRESETS_DIR = os.path.expanduser("~/.config/easyeffects/output")
EE_BIN = shutil.which("easyeffects") 

class VibeEQApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.geometry("550x700")
        
        self.bg_color = "#1a1a1a"
        self.accent = "#00e0a0"      
        self.warn = "#ff4444"
        self.sec_bg = "#2b2b2b"
        
        self.root.configure(bg=self.bg_color)
        self.root.attributes('-alpha', 0.95) 

        tk.Label(root, text="VIBE EQ", font=("Segoe UI", 26, "bold"), 
                 bg=self.bg_color, fg=self.accent).pack(pady=(30, 5))
        
        # --- VERIFICACIÓN DE SISTEMA ---
        self.check_frame = tk.Frame(root, bg=self.sec_bg, padx=10, pady=5)
        self.check_frame.pack(fill="x", padx=40, pady=10)
        
        if EE_BIN:
            status_text = "✔ SISTEMA LISTO: EasyEffects Detectado"
            status_fg = self.accent
            self.system_ready = True
        else:
            status_text = "❌ ERROR: No se encontró EasyEffects"
            status_fg = self.warn
            self.system_ready = False
            
        tk.Label(self.check_frame, text=status_text, font=("Consolas", 10, "bold"),
                 bg=self.sec_bg, fg=status_fg).pack()

        # Botón Importar
        self.btn_import = tk.Button(root, text="＋ IMPORTAR JSON", 
                               command=self.importar_json, 
                               bg=self.accent, fg="black", font=("Segoe UI", 11, "bold"),
                               relief="flat", cursor="hand2", state="normal" if self.system_ready else "disabled")
        self.btn_import.pack(fill="x", padx=40, pady=(20,10), ipady=5)

        # Lista
        tk.Label(root, text="Presets Instalados:", bg=self.bg_color, fg="#ccc", anchor="w").pack(fill="x", padx=40, pady=(10,5))
        
        frame_list = tk.Frame(root, bg=self.sec_bg)
        frame_list.pack(fill="both", expand=True, padx=40, pady=0)
        
        self.listbox = tk.Listbox(frame_list, bg=self.sec_bg, fg="white", 
                                  font=("Consolas", 11), bd=0, highlightthickness=0,
                                  selectbackground=self.accent, selectforeground="black")
        self.listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame_list, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        self.listbox.bind('<Double-1>', self.activar_preset)

        # Botón Activar
        self.btn_apply = tk.Button(root, text="▶ ACTIVAR SELECCIONADO", 
                              command=self.activar_preset, 
                              bg=self.sec_bg, fg=self.accent, font=("Segoe UI", 10, "bold"),
                              relief="flat", bd=1, cursor="hand2", state="normal" if self.system_ready else "disabled")
        self.btn_apply.pack(fill="x", padx=40, pady=20, ipady=5)

        tk.Label(root, text="NOTA: Reproduce música para ver las bandas moverse.", 
                 font=("Arial", 9), bg=self.bg_color, fg="#666").pack(side="bottom", pady=15)

        self.cargar_lista()

    def cargar_lista(self):
        self.listbox.delete(0, tk.END)
        if not self.system_ready: return
        rutas = [Path(EE_PRESETS_DIR), Path(os.path.expanduser("~/.local/share/easyeffects/output"))]
        encontrados = set()
        for ruta in rutas:
            if ruta.exists():
                for f in ruta.glob("*.json"): encontrados.add(f.stem)
        for arch in sorted(encontrados): self.listbox.insert(tk.END, arch)

    def activar_preset(self, event=None):
        if not self.system_ready: return
        seleccion = self.listbox.curselection()
        if not seleccion: return
        nombre = self.listbox.get(seleccion[0])
        self.aplicar_y_mostrar(nombre)

    def aplicar_y_mostrar(self, nombre):
        try:
            subprocess.run(["easyeffects", "-l", nombre], check=True)
            subprocess.Popen(["easyeffects"]) 
        except Exception as e:
            messagebox.showerror("Error", f"Fallo EasyEffects:\n{e}")

    def buscar_bandas_recursivo(self, data):
        if isinstance(data, list):
            if len(data) > 0 and isinstance(data[0], dict):
                keys = data[0].keys()
                if any(k in keys for k in ["frequency", "gain", "fc", "q", "preamp"]):
                    return data
            for item in data:
                res = self.buscar_bandas_recursivo(item)
                if res: return res
        elif isinstance(data, dict):
            for k in ["preset", "bands", "eq1", "entries", "equalizer"]:
                if k in data:
                    res = self.buscar_bandas_recursivo(data[k])
                    if res: return res
            for v in data.values():
                res = self.buscar_bandas_recursivo(v)
                if res: return res
        return None

    def importar_json(self):
        archivo = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not archivo: return
        try:
            with open(archivo, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
            nombre = Path(archivo).stem.replace(" ", "_")
            bandas = self.buscar_bandas_recursivo(raw_data)
            if not bandas: raise ValueError("Sin bandas de EQ válidas.")

            ee_data = {"output": {"blocklist": [], "plugins_order": ["equalizer"], "equalizer": {"left": {}, "right": {}, "num-bands": len(bandas)}}}
            for i, b in enumerate(bandas):
                k = f"band{i}"
                freq = b.get("frequency", b.get("fc", 100))
                gain = b.get("gain", b.get("g", 0.0))
                q_val = b.get("q", 1.0)
                info = { "type": "Bell", "mode": "RLC (BT)", "mute": False, "frequency": float(freq), "gain": float(gain), "q": float(q_val) }
                ee_data["output"]["equalizer"]["left"][k] = info
                ee_data["output"]["equalizer"]["right"][k] = info
            
            Path(EE_PRESETS_DIR).mkdir(parents=True, exist_ok=True)
            with open(os.path.join(EE_PRESETS_DIR, f"{nombre}.json"), 'w') as f: json.dump(ee_data, f, indent=4)
            self.cargar_lista()
            self.aplicar_y_mostrar(nombre) 
            messagebox.showinfo("ÉXITO", f"Preset '{nombre}' instalado.")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VibeEQApp(root)
    root.mainloop()

