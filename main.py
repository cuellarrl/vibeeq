#!/usr/bin/env python3
import os
import json
import subprocess
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

# --- CONFIGURACIÓN ---
APP_NAME = "VibeEQ Manager"
VERSION = "4.1.0 (Inspector)"
EE_PRESETS_DIR = os.path.expanduser("~/.config/easyeffects/output")

class VibeEQApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} {VERSION}")
        self.root.geometry("550x720")
        
        self.bg_color = "#1a1a1a"
        self.accent = "#00e0a0"      
        self.warn = "#ff4444"
        self.sec_bg = "#2b2b2b"
        
        self.root.configure(bg=self.bg_color)
        self.root.attributes('-alpha', 0.95) 

        tk.Label(root, text="VIBE EQ", font=("Segoe UI", 26, "bold"), 
                 bg=self.bg_color, fg=self.accent).pack(pady=(30, 5))

        # --- INSPECTOR DE DEPENDENCIAS ---
        self.check_frame = tk.Frame(root, bg=self.sec_bg, padx=10, pady=10)
        self.check_frame.pack(fill="x", padx=40, pady=10)

        # 1. Chequeo de EasyEffects
        ee_installed = shutil.which("easyeffects") is not None
        
        # 2. Chequeo de Plugins (LSP) - Específico para Arch/CachyOS
        lsp_installed = self.check_pacman_package("lsp-plugins")

        self.system_ready = ee_installed and lsp_installed

        if self.system_ready:
            msg = "✔ SISTEMA OPTIMIZADO\nEasyEffects + Plugins detectados"
            fg_color = self.accent
        else:
            msg = "⚠ FALTAN DEPENDENCIAS ⚠"
            fg_color = self.warn
            
        tk.Label(self.check_frame, text=msg, font=("Consolas", 11, "bold"),
                 bg=self.sec_bg, fg=fg_color).pack()

        # Mostrar qué falta exactamente
        if not self.system_ready:
            error_detail = ""
            if not ee_installed: error_detail += "- Falta: easyeffects\n"
            if not lsp_installed: error_detail += "- Falta: lsp-plugins (Motor de Audio)\n"
            
            tk.Label(self.check_frame, text=error_detail, justify="left",
                     bg=self.sec_bg, fg="#ccc").pack(pady=5)
            
            tk.Label(self.check_frame, text="EJECUTA ESTO EN TERMINAL:", 
                     bg=self.sec_bg, fg="white", font=("Arial", 8, "bold")).pack(pady=(5,0))
            
            # Caja de texto copiable con la solución
            cmd_solucion = "sudo pacman -S easyeffects lsp-plugins"
            entry = tk.Entry(self.check_frame, bg="black", fg=self.accent, justify="center")
            entry.insert(0, cmd_solucion)
            entry.pack(fill="x", padx=20, pady=5)

        # --- BOTONES (Se desactivan si no está listo el sistema) ---
        state_btn = "normal" if self.system_ready else "disabled"

        self.btn_import = tk.Button(root, text="＋ IMPORTAR JSON", 
                               command=self.importar_json, 
                               bg=self.accent, fg="black", font=("Segoe UI", 11, "bold"),
                               relief="flat", cursor="hand2", state=state_btn)
        self.btn_import.pack(fill="x", padx=40, pady=(20,10), ipady=5)

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

        self.btn_apply = tk.Button(root, text="▶ ACTIVAR SELECCIONADO", 
                              command=self.activar_preset, 
                              bg=self.sec_bg, fg=self.accent, font=("Segoe UI", 10, "bold"),
                              relief="flat", bd=1, cursor="hand2", state=state_btn)
        self.btn_apply.pack(fill="x", padx=40, pady=20, ipady=5)

        tk.Label(root, text="NOTA: Reproduce música para ver las bandas moverse.", 
                 font=("Arial", 9), bg=self.bg_color, fg="#666").pack(side="bottom", pady=15)

        if self.system_ready:
            self.cargar_lista()

    def check_pacman_package(self, pkg_name):
        """Verifica si un paquete está instalado en Arch/CachyOS"""
        try:
            # pacman -Q devuelve 0 si existe, 1 si no
            subprocess.run(["pacman", "-Q", pkg_name], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except subprocess.CalledProcessError:
            return False
        except FileNotFoundError:
            return False # Por si no tienes pacman (raro en CachyOS)

    def cargar_lista(self):
        self.listbox.delete(0, tk.END)
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
                if any(k in keys for k in ["frequency", "gain", "fc", "q", "preamp"]): return data
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
