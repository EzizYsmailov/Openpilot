"""
Universal CAN Dashboard
İslendik DBC faýly bilen işleýär.
Toyota DBC bolsa gözegçilik paneli görünýär.
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import threading
import time
import math
import os

from config import CAN_BITRATE, DEMO_MODE
from can_interface import CANInterface
from can_parser import CANParser
from toyota_commands import ToyotaCommander
import dbc_loader

# ── Reňkler ────────────────────────────────────────────────────────────
BG      = "#1e1e2e"
BG2     = "#2a2a3e"
BG3     = "#313145"
FG      = "#cdd6f4"
FG_DIM  = "#6c7086"
ACCENT  = "#89b4fa"
GREEN   = "#a6e3a1"
RED     = "#f38ba8"
YELLOW  = "#f9e2af"
ORANGE  = "#fab387"
PURPLE  = "#cba6f7"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Universal CAN Dashboard — opendbc")
        self.configure(bg=BG)
        self.minsize(900, 650)

        # Häzirki ýüklenmiş DBC
        self._db        = None
        self._db_info   = None
        self._parser    = None
        self._commander = None

        # Signal gymmatlar (internal_name → value)
        self._values    = {}
        self._lock      = threading.Lock()

        # Raw CAN data buffer (thread-safe → UI thread-de update edilýär)
        self._raw_buffer = []
        self._raw_lock   = threading.Lock()

        # CAN Interface
        self._can = CANInterface(on_message=self._on_can_msg)

        # Safety callback
        self._safety_alerts = []   # thread-safe safety alert buffer
        self._safety_lock = threading.Lock()

        self._build_ui()
        self._refresh_dbc_list()
        self._start_ui_update()

    # ==================================================================
    # UI Gurluşy
    # ==================================================================
    def _build_ui(self):
        # ── Başlyk ──────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG, pady=6)
        hdr.pack(fill='x', padx=10, pady=(8, 0))

        tk.Label(hdr, text="🚗  Universal CAN Dashboard",
                 bg=BG, fg=ACCENT, font=("Consolas", 14, "bold")).pack(side='left')

        self._lbl_status = tk.Label(hdr, text="● Birikmedik",
                                    bg=BG, fg=RED, font=("Consolas", 11))
        self._lbl_status.pack(side='right')

        # ── DBC Saýlaýjy ────────────────────────────────────────────
        dbc_frm = tk.LabelFrame(self, text=" 📂  DBC Faýly ",
                                bg=BG2, fg=PURPLE, font=("Consolas", 10, "bold"),
                                bd=1, relief='groove')
        dbc_frm.pack(fill='x', padx=10, pady=6)

        row1 = tk.Frame(dbc_frm, bg=BG2)
        row1.pack(fill='x', padx=8, pady=6)

        tk.Label(row1, text="Faýl:", bg=BG2, fg=FG_DIM,
                 font=("Consolas", 10)).pack(side='left')

        self._var_dbc = tk.StringVar()
        self._cb_dbc  = ttk.Combobox(row1, textvariable=self._var_dbc,
                                     width=35, state='readonly',
                                     font=("Consolas", 10))
        self._cb_dbc.pack(side='left', padx=6)

        tk.Button(row1, text="🔄 Täzele", bg=BG3, fg=FG,
                  font=("Consolas", 9), relief='flat', padx=6,
                  command=self._refresh_dbc_list).pack(side='left', padx=2)

        tk.Button(row1, text="📁 Gözle...", bg=BG3, fg=FG,
                  font=("Consolas", 9), relief='flat', padx=6,
                  command=self._browse_dbc).pack(side='left', padx=2)

        tk.Button(row1, text="✅ Ýükle", bg=ACCENT, fg="#000",
                  font=("Consolas", 10, "bold"), relief='flat', padx=8,
                  command=self._load_selected_dbc).pack(side='left', padx=6)

        # DBC info label
        self._lbl_dbc_info = tk.Label(dbc_frm, text="DBC ýüklenmedi",
                                      bg=BG2, fg=FG_DIM, font=("Consolas", 9))
        self._lbl_dbc_info.pack(padx=8, pady=(0, 4), anchor='w')

        # ── Baglanyş ────────────────────────────────────────────────
        con_frm = tk.Frame(self, bg=BG2, pady=6)
        con_frm.pack(fill='x', padx=10, pady=2)

        tk.Label(con_frm, text="Interface:", bg=BG2, fg=FG_DIM,
                 font=("Consolas", 10)).pack(side='left', padx=(8, 4))

        self._var_iface = tk.StringVar(value="ixxat")
        cb2 = ttk.Combobox(con_frm, textvariable=self._var_iface, width=14,
                           values=["ixxat", "demo", "socketcan", "pcan", "vector"],
                           state='readonly', font=("Consolas", 10))
        cb2.pack(side='left', padx=4)

        self._btn_conn = tk.Button(con_frm, text="Birikdir", bg=GREEN, fg="#000",
                                   font=("Consolas", 10, "bold"), relief='flat',
                                   padx=10, pady=2, command=self._toggle_connect)
        self._btn_conn.pack(side='left', padx=6)

        self._lbl_brand = tk.Label(con_frm, text="",
                                   bg=BG2, fg=ORANGE, font=("Consolas", 10, "bold"))
        self._lbl_brand.pack(side='right', padx=10)

        # ── Orta bölüm ──────────────────────────────────────────────
        mid = tk.Frame(self, bg=BG)
        mid.pack(fill='both', expand=True, padx=10, pady=4)

        self._build_dashboard(mid)
        self._build_raw_panel(mid)

        # ── Gözegçilik paneli (başda gizlin) ────────────────────────
        self._ctrl_frm = None
        self._build_control_panel()

        # ── Log ─────────────────────────────────────────────────────
        self._build_log()

    # ------------------------------------------------------------------
    def _build_dashboard(self, parent):
        self._dash_frm = tk.LabelFrame(parent, text=" 📊  Sensor Maglumatlary ",
                                       bg=BG2, fg=ACCENT, font=("Consolas", 10, "bold"),
                                       bd=1, relief='groove', width=280)
        self._dash_frm.pack(side='left', fill='y', padx=(0, 4))
        self._dash_frm.pack_propagate(False)

        # Tizlometr
        self._canvas = tk.Canvas(self._dash_frm, width=180, height=180,
                                 bg=BG2, highlightthickness=0)
        self._canvas.pack(pady=6)
        self._draw_gauge(0)

        # Dinamiki signal labellar — DBC ýüklenenden soň doldurylýar
        self._sig_frame = tk.Frame(self._dash_frm, bg=BG2)
        self._sig_frame.pack(fill='x', padx=8, pady=4)
        self._sig_labels = {}   # internal_name → (var, lbl_widget)

        self._lbl_no_dbc = tk.Label(self._sig_frame,
                                    text="DBC ýükle → signallar görüner",
                                    bg=BG2, fg=FG_DIM, font=("Consolas", 9))
        self._lbl_no_dbc.pack()

        # Safety status paneli
        safety_frm = tk.LabelFrame(self._dash_frm, text=" 🛡️  Howpsuzlyk ",
                                   bg=BG3, fg=PURPLE, font=("Consolas", 9, "bold"),
                                   bd=1, relief='groove')
        safety_frm.pack(fill='x', padx=6, pady=(4, 2))

        self._var_safety_engaged = tk.StringVar(value="● OFF")
        self._lbl_safety_engaged = tk.Label(safety_frm, textvariable=self._var_safety_engaged,
                                            bg=BG3, fg=FG_DIM, font=("Consolas", 10, "bold"))
        self._lbl_safety_engaged.pack(anchor='w', padx=4, pady=1)

        self._var_safety_info = tk.StringVar(value="")
        tk.Label(safety_frm, textvariable=self._var_safety_info,
                 bg=BG3, fg=FG_DIM, font=("Consolas", 8)).pack(anchor='w', padx=4, pady=1)

        self._var_rate_torque = tk.StringVar(value="Torque: 0")
        tk.Label(safety_frm, textvariable=self._var_rate_torque,
                 bg=BG3, fg=FG_DIM, font=("Consolas", 8)).pack(anchor='w', padx=4, pady=(0, 2))

    # ------------------------------------------------------------------
    def _rebuild_signal_labels(self):
        """DBC ýüklenensoň signal labellaryny täzeden gurýar"""
        for w in self._sig_frame.winfo_children():
            w.destroy()
        self._sig_labels.clear()

        if not self._db_info:
            return

        known = self._db_info['known']

        # Belli internal signal atlary → görkeziljek at
        display_names = {
            'speed':       ("Tizlik",         "km/h", ACCENT),
            'steer_angle': ("Ruletka",         "°",    YELLOW),
            'gas_pct':     ("Gaz pedaly",      "%",    GREEN),
            'brake':       ("Tormoz",          "",     RED),
            'rpm':         ("Motor RPM",       "rpm",  FG),
            'cruise':      ("Kruiz",           "",     ORANGE),
            'cruise_state':("Kruiz Ýag.",      "",     ORANGE),
            'wheel_FL':    ("Sol Ön tigir",    "km/h", FG),
            'wheel_FR':    ("Sag Ön tigir",    "km/h", FG),
            'wheel_RL':    ("Sol Art tigir",   "km/h", FG),
            'wheel_RR':    ("Sag Art tigir",   "km/h", FG),
            'driver_torq': ("Sürüji Torque",   "",     FG),
            'steer_ovrrd': ("Steer Override",  "",     PURPLE),
        }

        grid = tk.Frame(self._sig_frame, bg=BG2)
        grid.pack(fill='x')

        row = 0
        for internal, (disp, unit, color) in display_names.items():
            if internal not in known:
                continue
            tk.Label(grid, text=disp + ":", bg=BG2, fg=FG_DIM,
                     font=("Consolas", 9), anchor='w', width=15).grid(
                row=row, column=0, sticky='w', pady=1)
            var = tk.StringVar(value="--")
            tk.Label(grid, textvariable=var, bg=BG2, fg=color,
                     font=("Consolas", 10, "bold"), anchor='e', width=9).grid(
                row=row, column=1, sticky='e')
            if unit:
                tk.Label(grid, text=unit, bg=BG2, fg=FG_DIM,
                         font=("Consolas", 8), anchor='w', width=5).grid(
                    row=row, column=2, sticky='w')
            self._sig_labels[internal] = var
            row += 1

        if not self._sig_labels:
            tk.Label(grid, text="Belli signal tapylmady",
                     bg=BG2, fg=FG_DIM, font=("Consolas", 9)).grid(row=0, column=0, columnspan=3)

    # ------------------------------------------------------------------
    def _build_raw_panel(self, parent):
        """Ähli CAN habarlary raw görkeziş paneli"""
        frm = tk.LabelFrame(parent, text=" 🔍  Raw CAN Habarlary ",
                            bg=BG2, fg=FG_DIM, font=("Consolas", 10, "bold"),
                            bd=1, relief='groove')
        frm.pack(side='left', fill='both', expand=True, padx=(0, 4))

        # Habar agajy (Treeview)
        cols = ('ID', 'Habar', 'Signal', 'Gymmaty', 'Birlik')
        self._tree = ttk.Treeview(frm, columns=cols, show='headings', height=14)
        for col in cols:
            self._tree.heading(col, text=col)
        self._tree.column('ID',      width=70,  anchor='center')
        self._tree.column('Habar',   width=130, anchor='w')
        self._tree.column('Signal',  width=160, anchor='w')
        self._tree.column('Gymmaty', width=90,  anchor='e')
        self._tree.column('Birlik',  width=50,  anchor='center')

        # Reňk temalary
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Treeview",
                        background=BG3, foreground=FG,
                        fieldbackground=BG3, rowheight=20,
                        font=("Consolas", 9))
        style.configure("Treeview.Heading",
                        background=BG2, foreground=ACCENT,
                        font=("Consolas", 9, "bold"))
        style.map("Treeview", background=[('selected', BG)])

        sb = ttk.Scrollbar(frm, orient='vertical', command=self._tree.yview)
        self._tree.configure(yscrollcommand=sb.set)
        self._tree.pack(side='left', fill='both', expand=True)
        sb.pack(side='right', fill='y')

        self._tree_rows = {}   # (msg_id, sig_name) → tree item id

    # ------------------------------------------------------------------
    def _build_control_panel(self):
        """Toyota gözegçilik paneli — diňe Toyota DBC bolsa görünýär"""
        self._ctrl_frm = tk.LabelFrame(self, text=" 🎮  Toyota Gözegçilik ",
                                       bg=BG2, fg=YELLOW,
                                       font=("Consolas", 10, "bold"),
                                       bd=1, relief='groove')
        # pack edilmeýär — diňe Toyota DBC bolsa görüner

        # Steer
        tk.Label(self._ctrl_frm, text="Ruly:",
                 bg=BG2, fg=YELLOW, font=("Consolas", 10, "bold")).grid(
            row=0, column=0, padx=8, pady=4, sticky='w')

        self._var_steer = tk.IntVar(value=0)
        tk.Scale(self._ctrl_frm, from_=-1500, to=1500, orient='horizontal',
                 variable=self._var_steer, bg=BG2, fg=YELLOW, troughcolor=BG3,
                 highlightthickness=0, length=220, font=("Consolas", 9),
                 command=self._on_steer_change).grid(row=0, column=1, padx=4)

        btn_row = tk.Frame(self._ctrl_frm, bg=BG2)
        btn_row.grid(row=1, column=0, columnspan=2, pady=2)
        tk.Button(btn_row, text="◀ Çepe", bg=BG3, fg=YELLOW,
                  font=("Consolas", 9), relief='flat', padx=5,
                  command=lambda: self._set_steer(-600)).pack(side='left', padx=3)
        tk.Button(btn_row, text="⏹ Dur", bg=RED, fg='white',
                  font=("Consolas", 9), relief='flat', padx=5,
                  command=lambda: self._set_steer(0)).pack(side='left', padx=3)
        tk.Button(btn_row, text="Saga ▶", bg=BG3, fg=YELLOW,
                  font=("Consolas", 9), relief='flat', padx=5,
                  command=lambda: self._set_steer(600)).pack(side='left', padx=3)

        # Accel
        tk.Label(self._ctrl_frm, text="Tizlik:",
                 bg=BG2, fg=GREEN, font=("Consolas", 10, "bold")).grid(
            row=2, column=0, padx=8, pady=4, sticky='w')

        self._var_accel = tk.DoubleVar(value=0.0)
        tk.Scale(self._ctrl_frm, from_=-3.5, to=2.0, resolution=0.1,
                 orient='horizontal', variable=self._var_accel,
                 bg=BG2, fg=GREEN, troughcolor=BG3, highlightthickness=0,
                 length=220, font=("Consolas", 9),
                 command=self._on_accel_change).grid(row=2, column=1, padx=4)

        btn_row2 = tk.Frame(self._ctrl_frm, bg=BG2)
        btn_row2.grid(row=3, column=0, columnspan=2, pady=2)
        tk.Button(btn_row2, text="▲ Tizlendir", bg=BG3, fg=GREEN,
                  font=("Consolas", 9), relief='flat', padx=5,
                  command=lambda: self._set_accel(1.5)).pack(side='left', padx=3)
        tk.Button(btn_row2, text="⏹ Dur", bg=RED, fg='white',
                  font=("Consolas", 9), relief='flat', padx=5,
                  command=lambda: self._set_accel(0)).pack(side='left', padx=3)
        tk.Button(btn_row2, text="▼ Haýalla", bg=BG3, fg=RED,
                  font=("Consolas", 9), relief='flat', padx=5,
                  command=lambda: self._set_accel(-2.0)).pack(side='left', padx=3)

        # Acil
        tk.Button(self._ctrl_frm, text="🚨 HEMME DUR",
                  bg="#ff0000", fg="white", font=("Consolas", 10, "bold"),
                  relief='flat', padx=6, pady=4,
                  command=self._emergency_stop).grid(
            row=4, column=0, columnspan=2, pady=(6, 4), padx=10, sticky='ew')

    # ------------------------------------------------------------------
    def _build_log(self):
        frm = tk.LabelFrame(self, text=" 📝  Log ",
                            bg=BG2, fg=ACCENT, font=("Consolas", 10, "bold"),
                            bd=1, relief='groove')
        frm.pack(fill='x', padx=10, pady=(0, 8))
        self._log = scrolledtext.ScrolledText(frm, height=4, bg=BG3, fg=FG,
                                              font=("Consolas", 9), state='disabled')
        self._log.pack(fill='x', padx=4, pady=4)

    # ==================================================================
    # Gauge
    # ==================================================================
    def _draw_gauge(self, speed):
        c  = self._canvas
        cx, cy, r = 90, 90, 75
        c.delete("all")
        c.create_arc(cx-r, cy-r, cx+r, cy+r,
                     start=225, extent=-270, style='arc',
                     outline=BG3, width=10)
        pct = min(speed / 200.0, 1.0)
        if speed > 0:
            col = GREEN if speed < 100 else (YELLOW if speed < 150 else RED)
            c.create_arc(cx-r, cy-r, cx+r, cy+r,
                         start=225, extent=-int(270*pct), style='arc',
                         outline=col, width=10)
        ang = math.radians(225 - 270*pct)
        c.create_line(cx, cy,
                      cx + (r-15)*math.cos(ang),
                      cy - (r-15)*math.sin(ang),
                      fill=FG, width=2)
        c.create_oval(cx-4, cy-4, cx+4, cy+4, fill=ACCENT, outline="")
        c.create_text(cx, cy+22, text=f"{speed:.0f}",
                      fill=FG, font=("Consolas", 18, "bold"))
        c.create_text(cx, cy+40, text="km/h",
                      fill=FG_DIM, font=("Consolas", 9))

    # ==================================================================
    # DBC Işlemleri
    # ==================================================================
    def _refresh_dbc_list(self):
        files = dbc_loader.find_dbc_files()
        self._cb_dbc['values'] = files
        if files and not self._var_dbc.get():
            self._var_dbc.set(files[0])
        self._log_write(f"DBC faýllar tapyldy: {len(files)} sany — {files}")

    def _browse_dbc(self):
        path = filedialog.askopenfilename(
            title="DBC Faýlyny Saýla",
            filetypes=[("DBC files", "*.dbc"), ("All files", "*.*")],
            initialdir=os.path.dirname(os.path.abspath(__file__))
        )
        if path:
            # Faýly proýekt klasörüne göçür
            fname = os.path.basename(path)
            dest  = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
            if path != dest:
                import shutil
                try:
                    shutil.copy2(path, dest)
                    self._log_write(f"Göçürildi: {fname}")
                except Exception as e:
                    self._log_write(f"ÝALŇYŞLYK: Faýl göçürilmedi: {e}")
                    return
            self._refresh_dbc_list()
            self._var_dbc.set(fname)

    def _load_selected_dbc(self):
        fname = self._var_dbc.get()
        if not fname:
            self._log_write("DBC faýly saýlanmady!")
            return

        self._log_write(f"Ýüklenýär: {fname} ...")
        db, info = dbc_loader.load_dbc(fname)

        if db is None:
            self._log_write(f"ÝALŇYŞLYK: {info}")
            return

        self._db      = db
        self._db_info = info
        self._parser  = CANParser(db, info['known'])

        # UI täzele
        cap  = info['capabilities']
        brand = info['brand']
        self._lbl_brand.config(text=f"🚗 {brand}")
        self._lbl_dbc_info.config(
            fg=GREEN,
            text=(
                f"✅ {fname}  |  {brand}  |  "
                f"{info['msg_count']} habar  |  {info['sig_count']} signal  |  "
                f"Ruly: {'✅' if cap['steering'] else '❌'}  "
                f"Gaz: {'✅' if cap['accel'] else '❌'}"
            )
        )

        # Signal labellaryny täzele
        self._rebuild_signal_labels()
        self._values.clear()

        # Toyota gözegçilik panelini göster/gizle
        if cap['toyota_lka'] or cap['toyota_acc']:
            self._ctrl_frm.pack(fill='x', padx=10, pady=2)
            self._log_write("Toyota gözegçilik paneli açyldy (STEERING_LKA/ACC_CONTROL tapyldy)")
        else:
            self._ctrl_frm.pack_forget()
            self._log_write("Bu DBC Toyota gözegçiligini goldamaýar")

        # Treeview temizle
        for item in self._tree.get_children():
            self._tree.delete(item)
        self._tree_rows.clear()

        self._log_write(
            f"DBC ýüklendi: {fname} | {brand} | "
            f"{info['msg_count']} habar | {len(info['known'])} belli signal"
        )

    # ==================================================================
    # CAN Habary
    # ==================================================================
    def _on_can_msg(self, msg):
        if not self._parser:
            return

        # Safety layer-e CAN habary iber
        if self._commander:
            self._commander.feed_can_msg(msg)

        # Belli signallar
        result = self._parser.parse(msg)
        if result:
            with self._lock:
                self._values.update(result['values'])

        # Raw habar → buffer-e goş (UI thread-de update edilýär)
        raw = self._parser.parse_all(msg)
        if raw:
            with self._raw_lock:
                self._raw_buffer.append(raw)

    def _update_tree(self, raw):
        mid      = raw['msg_id']
        msg_name = raw['msg_name']
        for sig_name, val in raw['signals'].items():
            key = (mid, sig_name)
            try:
                msg_def = self._db.get_message_by_frame_id(mid)
                sig_def = next((s for s in msg_def.signals if s.name == sig_name), None)
                unit    = sig_def.unit if sig_def else ''
            except Exception:
                unit = ''

            row = (hex(mid), msg_name, sig_name, str(val), unit)
            if key in self._tree_rows:
                try:
                    self._tree.item(self._tree_rows[key], values=row)
                except Exception:
                    pass
            else:
                iid = self._tree.insert('', 'end', values=row)
                self._tree_rows[key] = iid

    # ==================================================================
    # UI Täzelemek (50ms)
    # ==================================================================
    def _start_ui_update(self):
        self._update_ui()

    def _update_ui(self):
        with self._lock:
            vals = dict(self._values)

        # Gauge
        speed = vals.get('speed', 0)
        self._draw_gauge(speed)

        # Signal labels
        for internal, var in self._sig_labels.items():
            if internal in vals:
                v = vals[internal]
                if isinstance(v, float):
                    if internal == 'steer_angle':
                        var.set(f"{v:+.1f}")
                    else:
                        var.set(f"{v:.1f}")
                else:
                    var.set(str(v))
            else:
                var.set("--")

        # Raw CAN buffer-i Treeview-a ýaz (thread-safe: diňe UI thread-de)
        with self._raw_lock:
            buffered = self._raw_buffer
            self._raw_buffer = []
        for raw in buffered:
            self._update_tree(raw)

        # Safety UI täzele
        self._update_safety_ui()

        # Safety alert-leri log-a ýaz (thread-safe)
        with self._safety_lock:
            alerts = list(self._safety_alerts)
            self._safety_alerts.clear()
        for reason in alerts:
            self._log_write(f"⚠️ DISENGAGE: {reason}")

        self.after(50, self._update_ui)

    def _update_safety_ui(self):
        """Safety ýagdaý GUI-ni täzele"""
        if not self._commander:
            self._var_safety_engaged.set("● OFF")
            self._lbl_safety_engaged.config(fg=FG_DIM)
            self._var_safety_info.set("")
            self._var_rate_torque.set("Torque: 0")
            return

        st = self._commander.get_safety_status()

        if st['engaged']:
            self._var_safety_engaged.set("● ENGAGED")
            self._lbl_safety_engaged.config(fg=GREEN)
        elif st['driver_override']:
            self._var_safety_engaged.set("● OVERRIDE")
            self._lbl_safety_engaged.config(fg=YELLOW)
        elif st['eps_fault']:
            self._var_safety_engaged.set("● EPS FAULT")
            self._lbl_safety_engaged.config(fg=RED)
        else:
            self._var_safety_engaged.set("● STANDBY")
            self._lbl_safety_engaged.config(fg=FG_DIM)

        info_parts = []
        if st['driver_override']:
            info_parts.append(f"Süriji: {st['driver_torque']}Nm")
        info_parts.append(f"LKA: {st['lka_state']}")
        if st['fault_count'] > 0:
            info_parts.append(f"Fault: {st['fault_count']}")
        self._var_safety_info.set(" | ".join(info_parts))

        self._var_rate_torque.set(f"Torque: {st['rate_limited_torque']}")

    # ==================================================================
    # Baglanyş
    # ==================================================================
    def _toggle_connect(self):
        if self._can.connected:
            if self._commander:
                self._commander.stop()
                self._commander = None
            self._can.disconnect()
            self._btn_conn.config(text="Birikdir", bg=GREEN)
            self._lbl_status.config(text="● Birikmedik", fg=RED)
            self._log_write("Kesildi.")
        else:
            if not self._parser:
                self._log_write("DUÝDURYŞ: DBC ýükleň öň — signallar görünmez!")

            iface = self._var_iface.get()
            import config as cfg
            cfg.DEMO_MODE = (iface == 'demo')
            cfg.CAN_INTERFACE = iface if iface != 'demo' else 'ixxat'

            try:
                self._can.connect()
                if self._db_info and (
                        self._db_info['capabilities']['toyota_lka'] or
                        self._db_info['capabilities']['toyota_acc']):
                    
                    # Dynamic Control IDs from DBC
                    c_ids = self._db_info.get('control_ids', {})
                    self._commander = ToyotaCommander(
                        self._can, 
                        steer_id=c_ids.get('STEERING_LKA'),
                        accel_id=c_ids.get('ACC_CONTROL')
                    )
                    
                    # Safety disengage callback
                    self._commander.safety.on_disengage = self._on_safety_disengage
                    self._commander.start()

                mode = "DEMO" if cfg.DEMO_MODE else iface.upper()
                self._btn_conn.config(text="Kes", bg=RED)
                self._lbl_status.config(text=f"● {mode} ✓", fg=GREEN)
                self._log_write(f"Birikdi! [{mode}] 🛡️ Safety aktiv")
            except Exception as e:
                self._log_write(f"ÝALŇYŞLYK: {e}")

    # ==================================================================
    # Gözegçilik
    # ==================================================================
    def _on_steer_change(self, val):
        t = int(float(val))
        if self._commander and abs(t) > 50:
            self._commander.set_steer(t)
        elif self._commander:
            self._commander.stop_steer()

    def _set_steer(self, torque):
        self._var_steer.set(torque)
        if self._commander:
            if abs(torque) > 0:
                self._commander.set_steer(torque)
            else:
                self._commander.stop_steer()
        self._log_write(f"Ruly: {torque:+d}")

    def _on_accel_change(self, val):
        a = float(val)
        if self._commander and abs(a) > 0.05:
            self._commander.set_accel(a)
        elif self._commander:
            self._commander.stop_accel()

    def _set_accel(self, val):
        self._var_accel.set(val)
        if self._commander:
            if abs(val) > 0.05:
                self._commander.set_accel(val)
            else:
                self._commander.stop_accel()
        self._log_write(f"Accel: {val:+.1f} m/s²")

    def _emergency_stop(self):
        if self._commander:
            self._commander.stop()
        self._var_steer.set(0)
        self._var_accel.set(0)
        self._log_write("🚨 HEMME DURDURYLDY!")

    # ==================================================================
    # Safety Callback
    # ==================================================================
    def _on_safety_disengage(self, reason: str):
        """Safety disengage bolanda çagyrylýar (CAN thread-den)"""
        with self._safety_lock:
            self._safety_alerts.append(reason)

    # ==================================================================
    # Log
    # ==================================================================
    def _log_write(self, text):
        ts = time.strftime("%H:%M:%S")
        self._log.config(state='normal')
        self._log.insert('end', f"[{ts}] {text}\n")
        # Log-y 500 setirden köp bolmaz ýaly käs
        line_count = int(self._log.index('end-1c').split('.')[0])
        if line_count > 500:
            self._log.delete('1.0', f"{line_count - 500}.0")
        self._log.see('end')
        self._log.config(state='disabled')

    def on_close(self):
        if self._commander:
            self._commander.stop()
        self._can.disconnect()
        self.destroy()

if __name__ == "__main__":
    app = App()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
