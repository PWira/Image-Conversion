"""
Aplikasi utama GUI untuk Image Resolver.
"""

import sys
import threading
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

from src.constants import OUTPUT_FORMATS, EXT_MAP, INPUT_EXTS
from src.image_processor import open_image, save_image, do_resize
from src.ui_components import Tooltip, int_or_none, float_or_none, filetypes_input


class App(tk.Tk):
    """Aplikasi GUI utama untuk konversi dan resize gambar."""
    
    def __init__(self):
        super().__init__()
        self.title("Image Converter & Resizer")
        self.resizable(False, False)
        self._set_icon()
        self._build_ui()
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        w  = self.winfo_width()
        h  = self.winfo_height()
        self.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")

    def _set_icon(self):
        """Set icon aplikasi jika monolight.png tersedia."""
        try:
            self.iconphoto(True, ImageTk.PhotoImage(Image.open("monolight.png")))
        except Exception:
            pass

    def _build_ui(self):
        """Build seluruh UI aplikasi."""
        PAD = dict(padx=10, pady=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=10, pady=(10, 0))

        self.tab_single = ttk.Frame(nb)
        self.tab_resize = ttk.Frame(nb)
        self.tab_batch  = ttk.Frame(nb)

        nb.add(self.tab_single, text="  Konversi  ")
        nb.add(self.tab_resize, text="  Resize  ")
        nb.add(self.tab_batch,  text="  Batch  ")

        self._build_single(self.tab_single, PAD)
        self._build_resize(self.tab_resize, PAD)
        self._build_batch(self.tab_batch, PAD)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=10, pady=(8, 0))

        # Log area
        log_frame = ttk.LabelFrame(self, text="Log", padding=6)
        log_frame.pack(fill="both", padx=10, pady=(4, 4))

        self.log = tk.Text(
            log_frame, height=6, font=("Courier New", 9),
            state="disabled", wrap="word",
            background="#f8f8f8", relief="flat"
        )
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        self.log.tag_config("ok",  foreground="#1D9E75")
        self.log.tag_config("err", foreground="#E24B4A")
        self.log.tag_config("inf", foreground="#185FA5")

        # Progress bar frame dengan label persentase
        prog_frame = ttk.Frame(self)
        prog_frame.pack(fill="x", padx=10, pady=(0, 8))
        self.progress = ttk.Progressbar(prog_frame, mode="determinate", maximum=100, length=400)
        self.progress.pack(fill="x", side="left", expand=True)
        self.progress_label = ttk.Label(prog_frame, text="0%", width=5)
        self.progress_label.pack(side="left", padx=(4, 0))

    def _build_single(self, parent, PAD):
        """Build tab Konversi."""
        self.s_src  = tk.StringVar()
        self.s_dst  = tk.StringVar()
        self.s_fmt  = tk.StringVar(value="PNG")
        self.s_qual = tk.IntVar(value=85)
        self.s_w    = tk.StringVar()
        self.s_h    = tk.StringVar()
        self.s_mode = tk.StringVar(value="Proporsional (fit)")

        f = ttk.Frame(parent, padding=8)
        f.pack(fill="both", expand=True)

        self._row(f, 0, "File input", self.s_src,
                  lambda: self._pick_src(self.s_src, self.s_dst, self.s_fmt))
        self._row(f, 1, "File output", self.s_dst,
                  lambda: self._save_as(self.s_dst, self.s_fmt))

        ttk.Separator(f, orient="h").grid(row=2, column=0, columnspan=3, sticky="ew", pady=6)

        # Format output
        ttk.Label(f, text="Format output").grid(row=3, column=0, sticky="w", **PAD)
        cb = ttk.Combobox(f, textvariable=self.s_fmt, values=OUTPUT_FORMATS,
                          state="readonly", width=12)
        cb.grid(row=3, column=1, sticky="w", **PAD)
        cb.bind("<<ComboboxSelected>>", lambda e: self._update_dst_ext(self.s_dst, self.s_fmt))

        # Kualitas
        ttk.Label(f, text="Kualitas").grid(row=4, column=0, sticky="w", **PAD)
        qf = ttk.Frame(f)
        qf.grid(row=4, column=1, columnspan=2, sticky="ew", **PAD)
        ttk.Scale(qf, from_=1, to=100, variable=self.s_qual, orient="horizontal", length=200,
                  command=lambda v: self.s_qual.set(int(float(v)))).pack(side="left")
        ttk.Label(qf, textvariable=self.s_qual, width=3).pack(side="left", padx=4)
        Tooltip(qf, "Hanya berlaku untuk JPEG, WEBP, AVIF")

        ttk.Separator(f, orient="h").grid(row=5, column=0, columnspan=3, sticky="ew", pady=6)
        ttk.Label(f, text="Resize (opsional)", font=("Segoe UI", 9, "bold")
                  ).grid(row=6, column=0, columnspan=3, sticky="w", **PAD)

        ttk.Label(f, text="Lebar (px)").grid(row=7, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.s_w, width=12).grid(row=7, column=1, sticky="w", **PAD)
        ttk.Label(f, text="Tinggi (px)").grid(row=8, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.s_h, width=12).grid(row=8, column=1, sticky="w", **PAD)

        ttk.Label(f, text="Mode resize").grid(row=9, column=0, sticky="w", **PAD)
        ttk.Combobox(f, textvariable=self.s_mode, state="readonly", width=20,
                     values=["Proporsional (fit)", "Tepat (exact)",
                             "Thumbnail (crop)", "Persentase (%)"]
                     ).grid(row=9, column=1, sticky="w", **PAD)

        ttk.Button(f, text="Konversi Sekarang", command=self._run_single
                   ).grid(row=10, column=0, columnspan=3, pady=(10, 4), ipadx=20)
        f.columnconfigure(1, weight=1)

    def _build_resize(self, parent, PAD):
        """Build tab Resize."""
        self.r_src   = tk.StringVar()
        self.r_dst   = tk.StringVar()
        self.r_w     = tk.StringVar()
        self.r_h     = tk.StringVar()
        self.r_scale = tk.StringVar()
        self.r_maxw  = tk.StringVar()
        self.r_maxh  = tk.StringVar()
        self.r_mode  = tk.StringVar(value="Proporsional (fit)")
        self.r_qual  = tk.IntVar(value=90)

        f = ttk.Frame(parent, padding=8)
        f.pack(fill="both", expand=True)

        self._row(f, 0, "File input", self.r_src,
                  lambda: self._pick_src(self.r_src, self.r_dst, None))
        self._row(f, 1, "File output", self.r_dst,
                  lambda: self._save_as(self.r_dst, None))

        ttk.Separator(f, orient="h").grid(row=2, column=0, columnspan=3, sticky="ew", pady=6)

        # Resize parameters
        for row, lbl, var, tip in [
            (3, "Lebar (px)",  self.r_w,    "Kosongkan jika tidak dipakai"),
            (4, "Tinggi (px)", self.r_h,    "Kosongkan jika tidak dipakai"),
            (5, "Skala (%)",   self.r_scale,"Contoh: 50 = setengah ukuran"),
            (6, "Maks lebar",  self.r_maxw, "Batas lebar maksimal"),
            (7, "Maks tinggi", self.r_maxh, "Batas tinggi maksimal"),
        ]:
            ttk.Label(f, text=lbl).grid(row=row, column=0, sticky="w", **PAD)
            e = ttk.Entry(f, textvariable=var, width=12)
            e.grid(row=row, column=1, sticky="w", **PAD)
            Tooltip(e, tip)

        ttk.Label(f, text="Mode").grid(row=8, column=0, sticky="w", **PAD)
        ttk.Combobox(f, textvariable=self.r_mode, state="readonly", width=20,
                     values=["Proporsional (fit)", "Tepat (exact)", "Thumbnail (crop)"]
                     ).grid(row=8, column=1, sticky="w", **PAD)

        # Kualitas
        ttk.Label(f, text="Kualitas").grid(row=9, column=0, sticky="w", **PAD)
        qf = ttk.Frame(f)
        qf.grid(row=9, column=1, sticky="ew", **PAD)
        ttk.Scale(qf, from_=1, to=100, variable=self.r_qual, orient="horizontal", length=180,
                  command=lambda v: self.r_qual.set(int(float(v)))).pack(side="left")
        ttk.Label(qf, textvariable=self.r_qual, width=3).pack(side="left", padx=4)

        ttk.Button(f, text="Resize Sekarang", command=self._run_resize
                   ).grid(row=10, column=0, columnspan=3, pady=(10, 4), ipadx=20)
        f.columnconfigure(1, weight=1)

    def _build_batch(self, parent, PAD):
        """Build tab Batch."""
        self.b_indir  = tk.StringVar()
        self.b_outdir = tk.StringVar()
        self.b_fmt    = tk.StringVar(value="PNG")
        self.b_qual   = tk.IntVar(value=85)
        self.b_w      = tk.StringVar()
        self.b_h      = tk.StringVar()
        self.b_scale  = tk.StringVar()
        self.b_rec    = tk.BooleanVar(value=False)

        f = ttk.Frame(parent, padding=8)
        f.pack(fill="both", expand=True)

        # Input/output directories
        ttk.Label(f, text="Folder input").grid(row=0, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_indir, width=30).grid(row=0, column=1, sticky="ew", **PAD)
        ttk.Button(f, text="Pilih...",
                   command=lambda: self.b_indir.set(filedialog.askdirectory() or self.b_indir.get())
                   ).grid(row=0, column=2, **PAD)

        ttk.Label(f, text="Folder output").grid(row=1, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_outdir, width=30).grid(row=1, column=1, sticky="ew", **PAD)
        ttk.Button(f, text="Pilih...",
                   command=lambda: self.b_outdir.set(filedialog.askdirectory() or self.b_outdir.get())
                   ).grid(row=1, column=2, **PAD)

        ttk.Separator(f, orient="h").grid(row=2, column=0, columnspan=3, sticky="ew", pady=6)

        # Format dan kualitas
        ttk.Label(f, text="Format output").grid(row=3, column=0, sticky="w", **PAD)
        ttk.Combobox(f, textvariable=self.b_fmt, values=OUTPUT_FORMATS,
                     state="readonly", width=12).grid(row=3, column=1, sticky="w", **PAD)

        ttk.Label(f, text="Kualitas").grid(row=4, column=0, sticky="w", **PAD)
        qf = ttk.Frame(f)
        qf.grid(row=4, column=1, sticky="ew", **PAD)
        ttk.Scale(qf, from_=1, to=100, variable=self.b_qual, orient="horizontal", length=180,
                  command=lambda v: self.b_qual.set(int(float(v)))).pack(side="left")
        ttk.Label(qf, textvariable=self.b_qual, width=3).pack(side="left", padx=4)

        ttk.Separator(f, orient="h").grid(row=5, column=0, columnspan=3, sticky="ew", pady=6)

        # Resize parameters
        ttk.Label(f, text="Lebar (px)").grid(row=6, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_w, width=12).grid(row=6, column=1, sticky="w", **PAD)
        ttk.Label(f, text="Tinggi (px)").grid(row=7, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_h, width=12).grid(row=7, column=1, sticky="w", **PAD)
        ttk.Label(f, text="Skala (%)").grid(row=8, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_scale, width=12).grid(row=8, column=1, sticky="w", **PAD)

        # Recursive option
        ttk.Checkbutton(f, text="Masuk subfolder (recursive)", variable=self.b_rec
                        ).grid(row=9, column=0, columnspan=3, sticky="w", **PAD)

        ttk.Button(f, text="Mulai Batch Konversi", command=self._run_batch
                   ).grid(row=10, column=0, columnspan=3, pady=(10, 4), ipadx=20)
        f.columnconfigure(1, weight=1)

    def _row(self, parent, row, label, var, cmd):
        """Helper untuk membuat row dengan label, entry, dan button."""
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Entry(parent, textvariable=var, width=32).grid(row=row, column=1,
                                                            sticky="ew", padx=4, pady=4)
        ttk.Button(parent, text="Pilih...", command=cmd, width=8).grid(row=row, column=2,
                                                                         padx=4, pady=4)

    def _update_dst_ext(self, dst_var, fmt_var):
        """Update ekstensi file output sesuai format."""
        dst = dst_var.get()
        if dst:
            new_ext = EXT_MAP.get(fmt_var.get(), Path(dst).suffix)
            dst_var.set(str(Path(dst).with_suffix(new_ext)))

    def _pick_src(self, src_var, dst_var, fmt_var):
        """Pick file input dan auto-generate output path."""
        path = filedialog.askopenfilename(filetypes=filetypes_input())
        if not path:
            return
        src_var.set(path)
        if dst_var and fmt_var:
            p = Path(path)
            ext = EXT_MAP.get(fmt_var.get(), ".png")
            dst_var.set(str(p.parent / (p.stem + "_result" + ext)))
        elif dst_var:
            p = Path(path)
            dst_var.set(str(p.parent / (p.stem + "_resized" + p.suffix)))

    def _save_as(self, dst_var, fmt_var):
        """Save as dialog untuk memilih path output."""
        fmt = fmt_var.get() if fmt_var else None
        if fmt:
            ext = EXT_MAP.get(fmt, ".png")
            filetypes = [(fmt, f"*{ext}"), ("Semua file", "*.*")]
            defext = ext
        else:
            filetypes = [("Semua gambar", " ".join(f"*{e}" for e in sorted(EXT_MAP.values()))),
                         ("Semua file", "*.*")]
            defext = ".png"
        path = filedialog.asksaveasfilename(filetypes=filetypes, defaultextension=defext)
        if path:
            dst_var.set(path)

    def _log(self, msg: str, tag: str = ""):
        """Tulis pesan ke log widget."""
        def _write():
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n", tag)
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, _write)

    def _update_progress(self, value: int):
        """Update progress bar ke nilai tertentu (0-100)."""
        def _update():
            self.progress["value"] = value
            self.progress_label.config(text=f"{value}%")
            self.update_idletasks()
        self.after(0, _update)

    def _set_progress(self, running: bool):
        """Set progress bar running atau stopped."""
        def _toggle():
            if running:
                self._update_progress(0)
            else:
                self._update_progress(100)
                self.after(500, lambda: self._update_progress(0))
        self.after(0, _toggle)

    @staticmethod
    def _mode_str(mode_label: str) -> str:
        """Convert mode label ke mode string untuk processing."""
        return {
            "Proporsional (fit)": "fit",
            "Tepat (exact)":      "exact",
            "Thumbnail (crop)":   "thumbnail",
        }.get(mode_label, "fit")

    def _run_single(self):
        """Runner untuk konversi satu file."""
        src = self.s_src.get().strip()
        dst = self.s_dst.get().strip()
        if not src or not dst:
            messagebox.showwarning("Input kurang", "Pilih file input dan output terlebih dahulu.")
            return

        fmt   = self.s_fmt.get()
        qual  = self.s_qual.get()
        w     = int_or_none(self.s_w.get())
        h     = int_or_none(self.s_h.get())
        mode  = self._mode_str(self.s_mode.get())
        scale = None
        if "Persentase" in self.s_mode.get():
            scale = float_or_none(self.s_w.get())
            if scale:
                scale = scale / 100
            w = h = None

        def task():
            self._set_progress(True)
            try:
                self._update_progress(10)
                is_svg = Path(src).suffix.lower() == ".svg"
                if is_svg:
                    img = open_image(Path(src), svg_width=w, svg_height=h, svg_scale=scale)
                else:
                    img = open_image(Path(src))
                    self._update_progress(40)
                    if w or h or scale:
                        img = do_resize(img, width=w, height=h, scale=scale, mode=mode)
                self._update_progress(70)
                ext   = EXT_MAP.get(fmt, Path(dst).suffix)
                dst_p = Path(dst).with_suffix(ext)
                save_image(img, dst_p, quality=qual, fmt_override=fmt)
                self._update_progress(100)
                self._log(f"✓  {Path(src).name}  →  {dst_p.name}  {img.size}", "ok")
            except Exception as e:
                self._log(f"✗  {e}", "err")
                traceback.print_exc()
            finally:
                self._set_progress(False)

        threading.Thread(target=task, daemon=True).start()

    def _run_resize(self):
        """Runner untuk resize file."""
        src = self.r_src.get().strip()
        dst = self.r_dst.get().strip()
        if not src or not dst:
            messagebox.showwarning("Input kurang", "Pilih file input dan output terlebih dahulu.")
            return

        w         = int_or_none(self.r_w.get())
        h         = int_or_none(self.r_h.get())
        maxw      = int_or_none(self.r_maxw.get())
        maxh      = int_or_none(self.r_maxh.get())
        scale_pct = float_or_none(self.r_scale.get())
        scale     = (scale_pct / 100) if scale_pct else None
        mode      = self._mode_str(self.r_mode.get())
        qual      = self.r_qual.get()

        def task():
            self._set_progress(True)
            try:
                self._update_progress(10)
                is_svg = Path(src).suffix.lower() == ".svg"
                if is_svg:
                    img = open_image(Path(src), svg_width=w, svg_height=h, svg_scale=scale)
                else:
                    img = open_image(Path(src))
                    self._update_progress(40)
                    img = do_resize(img, width=w, height=h, scale=scale,
                                    max_w=maxw, max_h=maxh, mode=mode)
                self._update_progress(70)
                save_image(img, Path(dst), quality=qual)
                self._update_progress(100)
                self._log(f"✓  {Path(src).name}  →  {Path(dst).name}  {img.size}", "ok")
            except Exception as e:
                self._log(f"✗  {e}", "err")
            finally:
                self._set_progress(False)

        threading.Thread(target=task, daemon=True).start()

    def _run_batch(self):
        """Runner untuk batch konversi."""
        indir  = self.b_indir.get().strip()
        outdir = self.b_outdir.get().strip()
        if not indir or not outdir:
            messagebox.showwarning("Input kurang", "Pilih folder input dan output.")
            return

        fmt       = self.b_fmt.get()
        qual      = self.b_qual.get()
        ext_out   = EXT_MAP.get(fmt, ".png")
        w         = int_or_none(self.b_w.get())
        h         = int_or_none(self.b_h.get())
        scale_pct = float_or_none(self.b_scale.get())
        scale     = (scale_pct / 100) if scale_pct else None
        recursive = self.b_rec.get()
        pattern   = "**/*" if recursive else "*"

        def task():
            self._set_progress(True)
            ok_count = err_count = 0
            in_p  = Path(indir)
            out_p = Path(outdir)
            files = [f for f in sorted(in_p.glob(pattern))
                     if f.is_file() and f.suffix.lower() in INPUT_EXTS]
            self._log(f"→  {len(files)} file ditemukan di {indir}", "inf")
            total = len(files)
            for idx, f in enumerate(files, 1):
                dst = out_p / (f.stem + ext_out)
                try:
                    is_svg = f.suffix.lower() == ".svg"
                    if is_svg:
                        img = open_image(f, svg_width=w, svg_height=h, svg_scale=scale)
                    else:
                        img = open_image(f)
                        if w or h or scale:
                            img = do_resize(img, width=w, height=h, scale=scale)
                    save_image(img, dst, quality=qual, fmt_override=fmt)
                    self._log(f"✓  {f.name}  →  {dst.name}  {img.size}", "ok")
                    ok_count += 1
                except Exception as e:
                    self._log(f"✗  {f.name}: {e}", "err")
                    err_count += 1
                progress_pct = int((idx / total) * 100)
                self._update_progress(progress_pct)
            self._log(f"Selesai: {ok_count} berhasil, {err_count} gagal.", "inf")
            self._set_progress(False)

        threading.Thread(target=task, daemon=True).start()
