"""
⚡ PortScan Pro - Interface Gráfica Moderna para Varredura de Portas TCP
Construído com Python e Tkinter (sem dependências externas necessárias).
"""

import os
import sys
import time
import json
import csv
import queue
import socket
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional, List

# Tenta carregar DPI awareness no Windows para renderização nítida
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# Importa o motor de varredura
try:
    from scanner_core import (
        PortScanner,
        ScanResult,
        resolve_target,
        parse_port_range,
        COMMON_SERVICES
    )
except ImportError:
    # Se executado diretamente na mesma pasta
    from .scanner_core import (
        PortScanner,
        ScanResult,
        resolve_target,
        parse_port_range,
        COMMON_SERVICES
    )

# Paleta de cores moderna (Tema Dark / Tecnológico)
THEME = {
    "bg": "#181825",            # Fundo principal
    "card": "#1e1e2e",          # Fundo de cartões e áreas agrupadas
    "card_alt": "#313244",      # Fundo secundário
    "border": "#45475a",        # Linhas de divisão
    "text": "#cdd6f4",          # Texto padrão
    "text_dim": "#a6adc8",      # Texto secundário
    "text_bright": "#ffffff",   # Texto destacado
    "accent": "#89b4fa",        # Azul destaque
    "accent_hover": "#b4befe",  # Hover no azul
    "green": "#a6e3a1",         # Verde sucesso / Porta aberta
    "green_bg": "#1d2e24",      # Fundo verde translúcido
    "red": "#f38ba8",           # Vermelho / Cancelar / Fechada
    "red_bg": "#331f28",        # Fundo vermelho
    "yellow": "#f9e2af",        # Amarelo alerta
    "cyan": "#94e2d5",          # Ciano
}

PRESET_TOP_PORTS = "21, 22, 23, 25, 53, 80, 110, 135, 139, 143, 443, 445, 993, 995, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8000, 8080, 8443, 27017"
PRESET_WEB_DB = "80, 443, 8000, 8080, 8443, 8888, 9000, 3306, 5432, 1433, 1521, 6379, 27017"
PRESET_DEFAULT = "1-1024"
PRESET_ALL = "1-65535"

class PortScannerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("⚡ PortScan Pro - Varredor de Portas TCP")
        self.root.geometry("980x760")
        self.root.minsize(860, 640)
        self.root.configure(bg=THEME["bg"])

        # Estado da aplicação
        self.scanner: Optional[PortScanner] = None
        self.scan_thread: Optional[threading.Thread] = None
        self.ui_queue = queue.Queue()
        self.is_scanning = False
        self.start_time = 0.0
        self.all_results: List[ScanResult] = []

        # Estatísticas
        self.count_total = 0
        self.count_scanned = 0
        self.count_open = 0
        self.count_closed = 0

        self._configure_styles()
        self._build_ui()
        self._check_ui_queue()

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Configurações globais ttk
        style.configure(".", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI", 9))

        # Frames
        style.configure("TFrame", background=THEME["bg"])
        style.configure("Card.TFrame", background=THEME["card"], relief="flat")
        style.configure("Header.TFrame", background=THEME["card"])

        # Labels
        style.configure("TLabel", background=THEME["bg"], foreground=THEME["text"])
        style.configure("Card.TLabel", background=THEME["card"], foreground=THEME["text"])
        style.configure("Dim.TLabel", background=THEME["card"], foreground=THEME["text_dim"], font=("Segoe UI", 8))
        style.configure("MetricVal.TLabel", background=THEME["card"], foreground=THEME["text_bright"], font=("Segoe UI", 16, "bold"))
        style.configure("MetricValGreen.TLabel", background=THEME["card"], foreground=THEME["green"], font=("Segoe UI", 16, "bold"))
        style.configure("HeaderTitle.TLabel", background=THEME["card"], foreground=THEME["accent"], font=("Segoe UI", 15, "bold"))

        # Entry
        style.configure("TEntry", fieldbackground=THEME["card_alt"], foreground=THEME["text_bright"], insertcolor=THEME["text_bright"])

        # Checkbutton
        style.configure("TCheckbutton", background=THEME["card"], foreground=THEME["text"], focuscolor=THEME["accent"])
        style.map("TCheckbutton", background=[("active", THEME["card"])])

        # Progressbar
        style.configure("Accent.Horizontal.TProgressbar", background=THEME["accent"], troughcolor=THEME["card_alt"], bordercolor=THEME["border"])

        # Treeview (Resultados)
        style.configure("Treeview",
                        background=THEME["card"],
                        foreground=THEME["text"],
                        fieldbackground=THEME["card"],
                        rowheight=26,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading",
                        background=THEME["card_alt"],
                        foreground=THEME["text_bright"],
                        font=("Segoe UI", 9, "bold"),
                        relief="flat")
        style.map("Treeview",
                  background=[("selected", THEME["accent"])],
                  foreground=[("selected", "#11111b")])
        style.map("Treeview.Heading",
                  background=[("active", THEME["border"])])

        # Notebook
        style.configure("TNotebook", background=THEME["bg"], borderwidth=0)
        style.configure("TNotebook.Tab",
                        background=THEME["card_alt"],
                        foreground=THEME["text"],
                        padding=[12, 6],
                        font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab",
                  background=[("selected", THEME["card"])],
                  foreground=[("selected", THEME["accent"])])

    def _build_ui(self):
        # 1. CABEÇALHO
        header_frame = ttk.Frame(self.root, style="Header.TFrame", padding=(20, 14))
        header_frame.pack(fill=tk.X, padx=0, pady=(0, 10))

        title_box = ttk.Frame(header_frame, style="Header.TFrame")
        title_box.pack(side=tk.LEFT)
        ttk.Label(title_box, text="⚡ PortScan Pro", style="HeaderTitle.TLabel").pack(anchor=tk.W)
        ttk.Label(title_box, text="Scanner de Portas TCP Multithread • Rápido, Preciso e Seguro", style="Dim.TLabel").pack(anchor=tk.W)

        self.lbl_target_info = ttk.Label(header_frame, text="Alvo: Não definido", foreground=THEME["cyan"], background=THEME["card"], font=("Segoe UI", 9, "italic"))
        self.lbl_target_info.pack(side=tk.RIGHT, pady=4)

        # 2. CONTAINER DE CONFIGURAÇÕES (CARD SUPERIOR)
        cfg_card = ttk.Frame(self.root, style="Card.TFrame", padding=14)
        cfg_card.pack(fill=tk.X, padx=14, pady=(0, 10))

        # Linha 1: Alvo e Presets
        r1 = ttk.Frame(cfg_card, style="Card.TFrame")
        r1.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(r1, text="Alvo (IP ou Hostname):", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.ent_target = tk.Entry(r1, bg=THEME["card_alt"], fg=THEME["text_bright"], insertbackground=THEME["text_bright"],
                                   relief="flat", highlightbackground=THEME["border"], highlightcolor=THEME["accent"],
                                   highlightthickness=1, font=("Segoe UI", 10), width=24)
        self.ent_target.pack(side=tk.LEFT, padx=(0, 12))
        self.ent_target.insert(0, "127.0.0.1")

        ttk.Label(r1, text="Atalhos:", style="Dim.TLabel").pack(side=tk.LEFT, padx=(6, 4))
        self._create_pill_btn(r1, "Top 25 Portas", lambda: self._apply_preset(PRESET_TOP_PORTS))
        self._create_pill_btn(r1, "Web & DB", lambda: self._apply_preset(PRESET_WEB_DB))
        self._create_pill_btn(r1, "Padrão (1-1024)", lambda: self._apply_preset(PRESET_DEFAULT))
        self._create_pill_btn(r1, "Tudo (1-65535)", lambda: self._apply_preset(PRESET_ALL))

        # Linha 2: Portas, Concorrência, Timeout
        r2 = ttk.Frame(cfg_card, style="Card.TFrame")
        r2.pack(fill=tk.X, pady=(0, 8))

        ttk.Label(r2, text="Portas:", style="Card.TLabel", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(0, 6))
        self.ent_ports = tk.Entry(r2, bg=THEME["card_alt"], fg=THEME["text_bright"], insertbackground=THEME["text_bright"],
                                  relief="flat", highlightbackground=THEME["border"], highlightcolor=THEME["accent"],
                                  highlightthickness=1, font=("Segoe UI", 10), width=24)
        self.ent_ports.pack(side=tk.LEFT, padx=(0, 16))
        self.ent_ports.insert(0, "1-1024")

        ttk.Label(r2, text="Threads:", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self.spn_threads = tk.Spinbox(r2, from_=5, to=500, increment=25, width=5,
                                      bg=THEME["card_alt"], fg=THEME["text_bright"], relief="flat",
                                      buttonbackground=THEME["card_alt"])
        self.spn_threads.pack(side=tk.LEFT, padx=(0, 16))
        self.spn_threads.delete(0, tk.END)
        self.spn_threads.insert(0, "60")

        ttk.Label(r2, text="Timeout (s):", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 4))
        self.spn_timeout = tk.Spinbox(r2, from_=0.1, to=5.0, increment=0.2, format="%.1f", width=5,
                                      bg=THEME["card_alt"], fg=THEME["text_bright"], relief="flat",
                                      buttonbackground=THEME["card_alt"])
        self.spn_timeout.pack(side=tk.LEFT, padx=(0, 16))
        self.spn_timeout.delete(0, tk.END)
        self.spn_timeout.insert(0, "0.8")

        # Opções booleanas
        self.var_only_open = tk.BooleanVar(value=True)
        self.chk_only_open = ttk.Checkbutton(r2, text="Apenas abertas na tabela", variable=self.var_only_open, style="TCheckbutton")
        self.chk_only_open.pack(side=tk.LEFT, padx=(8, 12))

        self.var_grab_banner = tk.BooleanVar(value=False)
        self.chk_grab_banner = ttk.Checkbutton(r2, text="Capturar banner", variable=self.var_grab_banner, style="TCheckbutton")
        self.chk_grab_banner.pack(side=tk.LEFT)

        # Linha 3: Botões de Ação
        r3 = ttk.Frame(cfg_card, style="Card.TFrame")
        r3.pack(fill=tk.X, pady=(6, 0))

        self.btn_start = tk.Button(r3, text="▶ Iniciar Varredura", bg=THEME["green"], fg="#11111b",
                                   activebackground="#88cc83", activeforeground="#11111b",
                                   font=("Segoe UI", 10, "bold"), relief="flat", padx=16, pady=6,
                                   cursor="hand2", command=self.start_scan)
        self.btn_start.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = tk.Button(r3, text="⏹ Cancelar", bg=THEME["red"], fg="#11111b",
                                  activebackground="#e06c88", activeforeground="#11111b",
                                  font=("Segoe UI", 10, "bold"), relief="flat", padx=14, pady=6,
                                  cursor="hand2", state=tk.DISABLED, command=self.stop_scan)
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 14))

        self.btn_clear = tk.Button(r3, text="🗑 Limpar", bg=THEME["card_alt"], fg=THEME["text"],
                                   activebackground=THEME["border"], activeforeground=THEME["text_bright"],
                                   font=("Segoe UI", 9), relief="flat", padx=12, pady=6,
                                   cursor="hand2", command=self.clear_results)
        self.btn_clear.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_export = tk.Button(r3, text="💾 Exportar Relatório", bg=THEME["card_alt"], fg=THEME["text"],
                                    activebackground=THEME["border"], activeforeground=THEME["text_bright"],
                                    font=("Segoe UI", 9), relief="flat", padx=12, pady=6,
                                    cursor="hand2", command=self.export_results)
        self.btn_export.pack(side=tk.LEFT)

        # 3. CARDS DE MÉTRICAS / ESTATÍSTICAS
        metrics_frame = ttk.Frame(self.root, style="TFrame")
        metrics_frame.pack(fill=tk.X, padx=14, pady=(0, 8))

        self.card_scanned = self._create_metric_card(metrics_frame, "Analisadas", "0 / 0", "MetricVal.TLabel")
        self.card_open = self._create_metric_card(metrics_frame, "Portas Abertas", "0", "MetricValGreen.TLabel")
        self.card_closed = self._create_metric_card(metrics_frame, "Fechadas / Filt.", "0", "MetricVal.TLabel")
        self.card_time = self._create_metric_card(metrics_frame, "Tempo", "0.0s", "MetricVal.TLabel")
        self.card_speed = self._create_metric_card(metrics_frame, "Velocidade", "0 p/s", "MetricVal.TLabel")

        # 4. BARRA DE PROGRESSO
        prog_frame = ttk.Frame(self.root, style="TFrame")
        prog_frame.pack(fill=tk.X, padx=14, pady=(0, 8))

        self.progress_bar = ttk.Progressbar(prog_frame, orient=tk.HORIZONTAL, mode='determinate', style="Accent.Horizontal.TProgressbar")
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        self.lbl_progress_pct = ttk.Label(prog_frame, text="0%", font=("Segoe UI", 9, "bold"), width=5)
        self.lbl_progress_pct.pack(side=tk.RIGHT)

        # 5. NOTEBOOK / ABAS (TABELA DE RESULTADOS + LOGS)
        notebook_frame = ttk.Frame(self.root, style="TFrame")
        notebook_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        self.notebook = ttk.Notebook(notebook_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Aba 1: Tabela
        tab_table = ttk.Frame(self.notebook, style="Card.TFrame", padding=6)
        self.notebook.add(tab_table, text="  📋 Tabela de Portas  ")

        # Barra de filtro rápido dentro da aba tabela
        filter_bar = ttk.Frame(tab_table, style="Card.TFrame")
        filter_bar.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(filter_bar, text="🔍 Filtrar resultados:", style="Card.TLabel").pack(side=tk.LEFT, padx=(0, 6))
        self.ent_filter = tk.Entry(filter_bar, bg=THEME["card_alt"], fg=THEME["text_bright"],
                                   insertbackground=THEME["text_bright"], relief="flat",
                                   highlightbackground=THEME["border"], highlightcolor=THEME["accent"],
                                   highlightthickness=1, font=("Segoe UI", 9), width=25)
        self.ent_filter.pack(side=tk.LEFT)
        self.ent_filter.bind("<KeyRelease>", self._apply_filter)

        # Treeview com Scrollbar
        table_container = ttk.Frame(tab_table, style="Card.TFrame")
        table_container.pack(fill=tk.BOTH, expand=True)

        cols = ("port", "status", "service", "latency", "details")
        self.tree = ttk.Treeview(table_container, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("port", text="Porta")
        self.tree.heading("status", text="Status")
        self.tree.heading("service", text="Serviço / Protocolo")
        self.tree.heading("latency", text="Latência (ms)")
        self.tree.heading("details", text="Detalhes / Banner")

        self.tree.column("port", width=85, anchor=tk.CENTER)
        self.tree.column("status", width=105, anchor=tk.CENTER)
        self.tree.column("service", width=180, anchor=tk.W)
        self.tree.column("latency", width=110, anchor=tk.E)
        self.tree.column("details", width=340, anchor=tk.W)

        # Tags de cores para as linhas
        self.tree.tag_configure("open", foreground=THEME["green"], font=("Segoe UI", 9, "bold"))
        self.tree.tag_configure("closed", foreground=THEME["text_dim"])

        tree_scroll = ttk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Menu de contexto com botão direito
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=THEME["card"], fg=THEME["text_bright"],
                                    activebackground=THEME["accent"], activeforeground="#11111b")
        self.context_menu.add_command(label="Copiar Linha", command=self._copy_selected_row)
        self.context_menu.add_command(label="Copiar Host:Porta", command=self._copy_host_port)
        self.tree.bind("<Button-3>", self._show_context_menu)

        # Aba 2: Log Console
        tab_log = ttk.Frame(self.notebook, style="Card.TFrame", padding=6)
        self.notebook.add(tab_log, text="  📜 Console em Tempo Real  ")

        self.txt_log = tk.Text(tab_log, bg="#11111b", fg=THEME["text"], insertbackground=THEME["text_bright"],
                               font=("Consolas", 9), relief="flat", wrap=tk.WORD)
        log_scroll = ttk.Scrollbar(tab_log, orient=tk.VERTICAL, command=self.txt_log.yview)
        self.txt_log.configure(yscrollcommand=log_scroll.set)

        self.txt_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Tags de cores no console
        self.txt_log.tag_configure("info", foreground=THEME["accent"])
        self.txt_log.tag_configure("success", foreground=THEME["green"], font=("Consolas", 9, "bold"))
        self.txt_log.tag_configure("warn", foreground=THEME["yellow"])
        self.txt_log.tag_configure("error", foreground=THEME["red"])

        # 6. RODAPÉ DE STATUS
        footer = ttk.Frame(self.root, style="Header.TFrame", padding=(14, 6))
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        self.lbl_status = ttk.Label(footer, text="Pronto para iniciar.", style="Card.TLabel")
        self.lbl_status.pack(side=tk.LEFT)

        ttk.Label(footer, text="PortScan Pro v2.0 • Socket TCP", style="Dim.TLabel").pack(side=tk.RIGHT)

        # Log inicial de boas-vindas
        self._log("PortScan Pro inicializado com sucesso.", "info")
        self._log("Insira o alvo (IP ou nome de domínio) e clique em 'Iniciar Varredura'.\n", "info")

    def _create_pill_btn(self, parent, text, command):
        btn = tk.Button(parent, text=text, bg=THEME["card_alt"], fg=THEME["text"],
                        activebackground=THEME["border"], activeforeground=THEME["text_bright"],
                        font=("Segoe UI", 8), relief="flat", padx=7, pady=2,
                        cursor="hand2", command=command)
        btn.pack(side=tk.LEFT, padx=3)
        return btn

    def _create_metric_card(self, parent, title, initial_val, style_val):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(12, 8))
        card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        ttk.Label(card, text=title, style="Dim.TLabel").pack(anchor=tk.W)
        lbl_val = ttk.Label(card, text=initial_val, style=style_val)
        lbl_val.pack(anchor=tk.W, pady=(2, 0))
        return lbl_val

    def _apply_preset(self, port_str):
        self.ent_ports.delete(0, tk.END)
        self.ent_ports.insert(0, port_str)

    def _log(self, message: str, tag: str = "info"):
        timestamp = time.strftime("[%H:%M:%S] ")
        self.txt_log.insert(tk.END, timestamp, "dim")
        self.txt_log.insert(tk.END, message + "\n", tag)
        self.txt_log.see(tk.END)

    def _show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def _copy_selected_row(self):
        sel = self.tree.selection()
        if sel:
            values = self.tree.item(sel[0], "values")
            self.root.clipboard_clear()
            self.root.clipboard_append(" | ".join(str(v) for v in values))

    def _copy_host_port(self):
        sel = self.tree.selection()
        if sel:
            port = self.tree.item(sel[0], "values")[0]
            target = self.ent_target.get().strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(f"{target}:{port}")

    def clear_results(self):
        if self.is_scanning:
            messagebox.showwarning("Aviso", "Aguarde a varredura atual terminar ou cancele antes de limpar.")
            return
        self.tree.delete(*self.tree.get_children())
        self.txt_log.delete("1.0", tk.END)
        self.all_results.clear()
        self.count_total = 0
        self.count_scanned = 0
        self.count_open = 0
        self.count_closed = 0
        self.progress_bar["value"] = 0
        self.lbl_progress_pct.config(text="0%")
        self.card_scanned.config(text="0 / 0")
        self.card_open.config(text="0")
        self.card_closed.config(text="0")
        self.card_time.config(text="0.0s")
        self.card_speed.config(text="0 p/s")
        self.lbl_status.config(text="Resultados limpos.")
        self._log("Interface e dados limpos.", "info")

    def _apply_filter(self, event=None):
        query = self.ent_filter.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        only_open = self.var_only_open.get()

        for res in self.all_results:
            if only_open and not res.is_open:
                continue

            port_s = str(res.port)
            service_s = (res.service or "").lower()
            details_s = (res.banner or res.error_msg or "").lower()

            if query and (query not in port_s and query not in service_s and query not in details_s):
                continue

            status_str = "ABERTA" if res.is_open else "FECHADA"
            tag = "open" if res.is_open else "closed"
            details = res.banner if res.banner else ("-" if res.is_open else res.error_msg or "Recusada")

            self.tree.insert("", tk.END, values=(
                res.port,
                status_str,
                res.service or "-",
                f"{res.latency_ms:.1f}",
                details
            ), tags=(tag,))

    def start_scan(self):
        target_input = self.ent_target.get().strip()
        ports_input = self.ent_ports.get().strip()

        if not target_input:
            messagebox.showerror("Erro", "Por favor, digite um IP ou Hostname válido.")
            return

        if not ports_input:
            messagebox.showerror("Erro", "Por favor, especifique o intervalo de portas (ex: 1-1024 ou 80, 443).")
            return

        try:
            ports = parse_port_range(ports_input)
            if not ports:
                raise ValueError("Nenhuma porta válida encontrada.")
        except Exception as e:
            messagebox.showerror("Erro no intervalo de portas", f"Formato inválido: {e}")
            return

        try:
            threads = int(self.spn_threads.get().strip())
        except ValueError:
            threads = 50

        try:
            timeout = float(self.spn_timeout.get().strip())
        except ValueError:
            timeout = 0.8

        grab_banner = self.var_grab_banner.get()

        # Resolução de DNS em thread para não travar
        self.btn_start.config(state=tk.DISABLED)
        self.lbl_status.config(text=f"Resolvendo endereço '{target_input}'...")

        def resolve_and_run():
            try:
                ip, hostname = resolve_target(target_input)
                self.ui_queue.put(("RESOLVED", (target_input, ip, hostname, ports, threads, timeout, grab_banner)))
            except Exception as e:
                self.ui_queue.put(("ERROR", f"Não foi possível resolver o alvo '{target_input}': {e}"))

        threading.Thread(target=resolve_and_run, daemon=True).start()

    def _execute_scan_thread(self, target_input, ip, hostname, ports, threads, timeout, grab_banner):
        self.is_scanning = True
        self.start_time = time.perf_counter()
        self.count_total = len(ports)
        self.count_scanned = 0
        self.count_open = 0
        self.count_closed = 0
        self.all_results.clear()
        self.tree.delete(*self.tree.get_children())

        self.scanner = PortScanner(target_ip=ip, timeout=timeout, max_threads=threads, grab_banner=grab_banner)

        self._log(f"Iniciando varredura em {hostname} ({ip})", "info")
        self._log(f"Total de {len(ports)} portas com {threads} threads (timeout: {timeout}s)...", "info")

        def on_port_scanned(result: ScanResult, completed: int, total: int):
            self.ui_queue.put(("PROGRESS", (result, completed, total)))

        try:
            results = self.scanner.scan_ports(ports, callback=on_port_scanned)
            self.ui_queue.put(("FINISHED", (results, self.scanner.is_stopped())))
        except Exception as e:
            self.ui_queue.put(("ERROR", f"Erro durante a varredura: {e}"))

    def stop_scan(self):
        if self.scanner and self.is_scanning:
            self.lbl_status.config(text="Interrompendo varredura...")
            self.scanner.stop()
            self.btn_stop.config(state=tk.DISABLED)
            self._log("Cancelamento solicitado pelo usuário...", "warn")

    def _check_ui_queue(self):
        """Processa mensagens enviadas da thread em segundo plano com segurança na UI."""
        try:
            while True:
                msg_type, payload = self.ui_queue.get_nowait()
                if msg_type == "RESOLVED":
                    target_input, ip, hostname, ports, threads, timeout, grab_banner = payload
                    self.lbl_target_info.config(text=f"Alvo: {hostname} ({ip})")
                    self.btn_stop.config(state=tk.NORMAL)
                    self.progress_bar["maximum"] = len(ports)
                    self.progress_bar["value"] = 0
                    self.lbl_status.config(text=f"Escaneando {ip}...")

                    # Dispara a thread de escaneamento
                    self.scan_thread = threading.Thread(
                        target=self._execute_scan_thread,
                        args=(target_input, ip, hostname, ports, threads, timeout, grab_banner),
                        daemon=True
                    )
                    self.scan_thread.start()

                elif msg_type == "PROGRESS":
                    res, completed, total = payload
                    self.count_scanned = completed
                    self.all_results.append(res)

                    if res.is_open:
                        self.count_open += 1
                        self._log(f"[+] Porta {res.port}/TCP ABERTA ({res.service or 'Desconhecido'}) - {res.latency_ms:.1f}ms", "success")
                        # Insere na tabela
                        details = res.banner if res.banner else "-"
                        self.tree.insert("", tk.END, values=(
                            res.port, "ABERTA", res.service or "-", f"{res.latency_ms:.1f}", details
                        ), tags=("open",))
                    else:
                        self.count_closed += 1
                        if not self.var_only_open.get():
                            self.tree.insert("", tk.END, values=(
                                res.port, "FECHADA", "-", f"{res.latency_ms:.1f}", res.error_msg or "Recusada"
                            ), tags=("closed",))

                    # Atualiza métricas
                    pct = int((completed / total) * 100) if total > 0 else 0
                    self.progress_bar["value"] = completed
                    self.lbl_progress_pct.config(text=f"{pct}%")
                    self.card_scanned.config(text=f"{completed} / {total}")
                    self.card_open.config(text=str(self.count_open))
                    self.card_closed.config(text=str(self.count_closed))

                    elapsed = max(0.01, time.perf_counter() - self.start_time)
                    self.card_time.config(text=f"{elapsed:.1f}s")
                    speed = completed / elapsed
                    self.card_speed.config(text=f"{speed:.0f} p/s")

                elif msg_type == "FINISHED":
                    results, was_stopped = payload
                    self.is_scanning = False
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_stop.config(state=tk.DISABLED)

                    elapsed = time.perf_counter() - self.start_time
                    if was_stopped:
                        self.lbl_status.config(text=f"Varredura cancelada pelo usuário após {elapsed:.2f}s.")
                        self._log(f"Varredura cancelada. {self.count_open} portas abertas encontradas.", "warn")
                    else:
                        self.lbl_status.config(text=f"Concluído em {elapsed:.2f}s! {self.count_open} portas abertas encontradas.")
                        self._log(f"Varredura concluída em {elapsed:.2f}s. Total abertas: {self.count_open}", "success")

                elif msg_type == "ERROR":
                    self.is_scanning = False
                    self.btn_start.config(state=tk.NORMAL)
                    self.btn_stop.config(state=tk.DISABLED)
                    self.lbl_status.config(text="Erro.")
                    self._log(f"[ERRO] {payload}", "error")
                    messagebox.showerror("Erro", str(payload))

        except queue.Empty:
            pass

        # Reagenda a verificação da fila
        self.root.after(80, self._check_ui_queue)

    def export_results(self):
        if not self.all_results:
            messagebox.showinfo("Exportar", "Não há resultados para exportar. Execute uma varredura primeiro.")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV (*.csv)", "*.csv"),
                ("Arquivo de Texto (*.txt)", "*.txt"),
                ("JSON (*.json)", "*.json")
            ],
            title="Salvar Relatório de Varredura"
        )
        if not file_path:
            return

        try:
            target = self.ent_target.get().strip()
            if file_path.endswith(".json"):
                data = {
                    "target": target,
                    "target_info": self.lbl_target_info.cget("text"),
                    "total_scanned": len(self.all_results),
                    "open_count": self.count_open,
                    "results": [r.to_dict() for r in self.all_results]
                }
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)

            elif file_path.endswith(".csv"):
                with open(file_path, "w", newline="", encoding="utf-8-sig") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Porta", "Status", "Serviço", "Latência (ms)", "Detalhes"])
                    for r in self.all_results:
                        writer.writerow([
                            r.port,
                            "ABERTA" if r.is_open else "FECHADA",
                            r.service,
                            f"{r.latency_ms:.2f}",
                            r.banner or r.error_msg
                        ])

            else:  # TXT
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("=" * 60 + "\n")
                    f.write("RELATÓRIO DE VARREDURA DE PORTAS - PORTSCAN PRO\n")
                    f.write(f"Alvo: {target} | {self.lbl_target_info.cget('text')}\n")
                    f.write(f"Total Analisado: {len(self.all_results)} | Abertas: {self.count_open}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(f"{'PORTA':<8} {'STATUS':<10} {'SERVIÇO':<20} {'LATÊNCIA':<12} {'DETALHES'}\n")
                    f.write("-" * 60 + "\n")
                    for r in self.all_results:
                        if self.var_only_open.get() and not r.is_open:
                            continue
                        f.write(f"{r.port:<8} {'ABERTA' if r.is_open else 'FECHADA':<10} {r.service:<20} {f'{r.latency_ms:.1f}ms':<12} {r.banner or r.error_msg}\n")

            messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso para:\n{file_path}")
            self._log(f"Relatório salvo em: {file_path}", "info")
        except Exception as e:
            messagebox.showerror("Erro ao Exportar", f"Não foi possível salvar o arquivo: {e}")

def main():
    root = tk.Tk()
    app = PortScannerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
