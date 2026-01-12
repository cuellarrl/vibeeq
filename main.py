#!/usr/bin/env python3
import os
import json
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path

# --- CONFIGURACIÓN ---
APP_NAME = "VibeEQ Manager"
VERSION = "3.0.0"
# EasyEffects busca aquí o en .local/share. Usamos .config para compatibilidad.
EE_PRESETS_DIR = os.path.expanduser("~/.config/easyeffects/output")

class VibeEQApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME}")
        self.root.geometry("500x650")
        
        # --- ESTILO "GLASS/DARK" ---
        self.bg_color = "#1a1a1a"    # Negro suave
        self.fg_color = "#ffffff"    # Texto blanco
        self.accent = "#00e0a0"      # Verde Neon
        self.sec_bg = "#2b2b2b"      # Gris oscuro para cajas
        
        self.root.configure(bg=self.bg_color)
        # Transparencia ligera (el blur depende de tu compositor Linux)
        self.root.attributes('-alpha', 0.96) 

        # Título
        tk.Label(root, text="VIBE EQ", font=("Segoe UI", 24, "bold"), 
                 bg=self.bg_color, fg=self.accent).pack(pady=(25, 5))
        
        tk.Label(root, text="Gestor de Presets", font=("Segoe UI", 10), 
                 bg=self.bg_color, fg="#888").pack(pady=(0, 20))

        # --- BOTÓN IMPORTAR ---
        btn_import = tk.Button(root, text="＋ IMPORTAR PRESET (JSON)", 
                               command=self.importar_json, 
                               bg=self.accent, fg="black", font=("Segoe UI", 11, "bold"),
                               relief="flat", activebackground="#00b070", cursor="hand2")
        btn_import.pack(fill="x", padx=40, pady=10, ipady=5)

        # --- LISTA DE PRESETS ---
        tk.Label(root, text="Tus Ecualizaciones:", bg=self.bg_color, fg="#ccc", anchor="w").pack(fill="x", padx=40, pady=(20,5))
        
        frame_list = tk.Frame(root, bg=self.sec_bg)
        frame_list.pack(fill="both", expand=True, padx=40, pady=0)
        
        self.listbox = tk.Listbox(frame_list, bg=self.sec_bg, fg="white", 
                                  font=("Consolas", 11), bd=0, highlightthickness=0,
                                  selectbackground=self.accent, selectforeground="black")
        self.listbox.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        scrollbar = tk.Scrollbar(frame_list, command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)
        
        self.listbox.bind('<Double-1>', self.activar_preset) # Doble click activa

        # --- BOTÓN ACTIVAR ---
        btn_apply = tk.Button(root, text="▶ ACTIVAR SELECCIONADO", 
                              command=self.activar_preset, 
                              bg=self.sec_bg, fg=self.accent, font=("Segoe UI", 10, "bold"),
                              relief="flat", bd=1, activebackground="#333", cursor="hand2")
        btn_apply.pack(fill="x", padx=40, pady=20, ipady=5)

        self.cargar_lista()

    def cargar_lista(self):
        self.listbox.delete(0, tk.END)
        # Buscamos en ambas rutas por si acaso (config y local/share)
        rutas = [
            Path(EE_PRESETS_DIR),
            Path(os.path.expanduser("~/.local/share/easyeffects/output"))
        ]
        
        encontrados = set()
        for ruta in rutas:
            if ruta.exists():
                for f in ruta.glob("*.json"):
                    encontrados.add(f.stem)
        
        for arch in sorted(encontrados):
            self.listbox.insert(tk.END, arch)

    def activar_preset(self, event=None):
        seleccion = self.listbox.curselection()
        if not seleccion: 
            messagebox.showwarning("!", "Selecciona un preset de la lista.")
            return
            
        nombre = self.listbox.get(seleccion[0])
        try:
            # Comando para cargar en EasyEffects
            subprocess.run(["easyeffects", "-l", nombre], check=True)
            messagebox.showinfo("VibeEQ", f"Ecualización activada:\n{nombre}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar en EasyEffects:\n{e}")

    # --- LÓGICA DEL CAZADOR (Tu código funcional) ---
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
            
            # Usamos la lógica que ya funcionó
            bandas = self.buscar_bandas_recursivo(raw_data)

            if not bandas:
                raise ValueError("No se detectaron bandas de EQ en este archivo.")

            # Formato EasyEffects
            ee_data = {
                "output": {
                    "blocklist": [], 
                    "plugins_order": ["equalizer"],
                    "equalizer": { "left": {}, "right": {}, "num-bands": len(bandas) }
                }
            }

            for i, b in enumerate(bandas):
                k = f"band{i}"
                freq = b.get("frequency", b.get("fc", 100))
                gain = b.get("gain", b.get("g", 0.0))
                q_val = b.get("q", 1.0)

                info = { 
                    "type": "Bell", "mode": "RLC (BT)", "mute": False,
                    "frequency": float(freq), "gain": float(gain), "q": float(q_val) 
                }
                ee_data["output"]["equalizer"]["left"][k] = info
                ee_data["output"]["equalizer"]["right"][k] = info
            
            # Guardar
            Path(EE_PRESETS_DIR).mkdir(parents=True, exist_ok=True)
            with open(os.path.join(EE_PRESETS_DIR, f"{nombre}.json"), 'w') as f:
                json.dump(ee_data, f, indent=4)
            
            # Recargar lista y activar
            self.cargar_lista()
            subprocess.run(["easyeffects", "-l", nombre])
            messagebox.showinfo("ÉXITO", f"Preset '{nombre}' importado y activado.")

        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    root = tk.Tk()
    app = VibeEQApp(root)
    root.mainloop()
