import sys
import threading
import traceback
from pathlib import Path
from typing import Optional

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except ImportError:
    sys.exit("tkinter tidak tersedia. Pastikan Python diinstal dengan modul tkinter.")

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError:
    sys.exit("Pillow belum terinstal. Jalankan: pip install Pillow")


# ---------------------------------------------------------------------------
# Format output yang praktis dan umum dipakai
# ---------------------------------------------------------------------------
OUTPUT_FORMATS = [
    "PNG", "JPEG", "WEBP", "TIFF", "BMP", "GIF", "ICO", "ICNS",
    "JPEG2000", "TGA", "PCX", "PPM", "SGI", "AVIF", "QOI", "DDS",
]

# Ekstensi default untuk setiap format output
EXT_MAP = {
    "PNG":      ".png",
    "JPEG":     ".jpg",
    "WEBP":     ".webp",
    "TIFF":     ".tiff",
    "BMP":      ".bmp",
    "GIF":      ".gif",
    "ICO":      ".ico",
    "ICNS":     ".icns",
    "JPEG2000": ".jp2",
    "TGA":      ".tga",
    "PCX":      ".pcx",
    "PPM":      ".ppm",
    "SGI":      ".sgi",
    "AVIF":     ".avif",
    "QOI":      ".qoi",
    "DDS":      ".dds",
}

# Semua ekstensi input yang didukung Pillow + SVG + PDF
INPUT_EXTS = {
    # JPEG family
    ".jpg", ".jpeg", ".jfif", ".jpe",
    # PNG
    ".png", ".apng",
    # Web / modern
    ".webp", ".avif", ".avifs", ".qoi",
    # TIFF
    ".tiff", ".tif",
    # BMP
    ".bmp", ".dib",
    # GIF
    ".gif",
    # Icons
    ".ico", ".icns", ".cur",
    # JPEG 2000
    ".jp2", ".j2k", ".j2c", ".jpc", ".jpf", ".jpx",
    # TGA
    ".tga", ".icb", ".vda", ".vst",
    # Misc raster
    ".pcx", ".ppm", ".pbm", ".pgm", ".pnm", ".pfm",
    ".sgi", ".rgb", ".rgba", ".bw",
    ".dds", ".psd", ".xbm", ".xpm",
    ".dcx", ".msp", ".im",
    # EPS / PS
    ".eps", ".ps",
    # Vektor
    ".svg",
    # Dokumen
    ".pdf",
}

SVG_EXT = {".svg"}
PDF_EXT = {".pdf"}

# Format yang butuh konversi mode sebelum disimpan
NEEDS_RGB  = {"JPEG", "BMP", "PCX", "PPM", "SGI", "TGA", "DDS"}
NEEDS_RGBA = {"ICO", "ICNS"}
QUALITY_FMT = {"JPEG", "WEBP", "AVIF"}


# ---------------------------------------------------------------------------
# Core: buka gambar
# ---------------------------------------------------------------------------
def open_image(path: Path, page: int = 0,
               svg_width: Optional[int] = None,
               svg_height: Optional[int] = None,
               svg_scale: Optional[float] = None) -> Image.Image:
    ext = path.suffix.lower()

    if ext in SVG_EXT:
        try:
            import cairosvg
        except ImportError:
            raise ImportError("cairosvg belum terinstal: pip install cairosvg")
        from io import BytesIO
        kwargs = {}
        if svg_width:
            kwargs["output_width"] = svg_width
        if svg_height:
            kwargs["output_height"] = svg_height
        if svg_scale and not svg_width and not svg_height:
            kwargs["scale"] = svg_scale
        png_bytes = cairosvg.svg2png(url=str(path), **kwargs)
        return Image.open(BytesIO(png_bytes)).convert("RGBA")

    if ext in PDF_EXT:
        try:
            import fitz
        except ImportError:
            raise ImportError("pymupdf belum terinstal: pip install pymupdf")
        from io import BytesIO
        doc = fitz.open(str(path))
        pix = doc[page].get_pixmap(dpi=150)
        return Image.open(BytesIO(pix.tobytes("png")))

    return Image.open(path)


# core : simpan gambar
# ---------------------------------------------------------------------------
def save_image(img: Image.Image, dest: Path, quality: int = 90,
               fmt_override: Optional[str] = None) -> None:
    fmt = fmt_override or dest.suffix.lstrip(".").upper()
    if fmt == "JPG":
        fmt = "JPEG"
    if fmt in ("JP2", "J2K", "JPC", "JPF", "JPX"):
        fmt = "JPEG2000"

    dest.parent.mkdir(parents=True, exist_ok=True)

    # Konversi mode gambar sesuai kebutuhan format tujuan
    if fmt in NEEDS_RGB and img.mode not in ("RGB", "L"):
        if img.mode == "P":
            img = img.convert("RGBA")
        if img.mode in ("RGBA", "LA"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")
    elif fmt in NEEDS_RGBA and img.mode != "RGBA":
        img = img.convert("RGBA")

    kwargs = {}
    if fmt in QUALITY_FMT:
        kwargs["quality"] = quality
        kwargs["optimize"] = True
    if fmt == "PNG":
        kwargs["optimize"] = True

    img.save(str(dest), format=fmt, **kwargs)


# Core: resize
# ---------------------------------------------------------------------------
def do_resize(img: Image.Image, width=None, height=None, scale=None,
              max_w=None, max_h=None, mode="fit") -> Image.Image:
    ow, oh = img.size
    if scale:
        return img.resize((int(ow * scale), int(oh * scale)), Image.LANCZOS)
    if max_w or max_h:
        tw, th = ow, oh
        if max_w and tw > max_w:
            th = int(th * max_w / tw); tw = max_w
        if max_h and th > max_h:
            tw = int(tw * max_h / th); th = max_h
        return img.resize((tw, th), Image.LANCZOS)
    if width and height:
        if mode == "exact":
            return img.resize((width, height), Image.LANCZOS)
        if mode == "thumbnail":
            return ImageOps.fit(img, (width, height), Image.LANCZOS)
        r = min(width / ow, height / oh)
        return img.resize((int(ow * r), int(oh * r)), Image.LANCZOS)
    if width:
        return img.resize((width, int(oh * width / ow)), Image.LANCZOS)
    if height:
        return img.resize((int(ow * height / oh), height), Image.LANCZOS)
    return img

# Utilitas GUI
# ---------------------------------------------------------------------------
def int_or_none(val: str) -> Optional[int]:
    try:
        v = int(val.strip())
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None

def float_or_none(val: str) -> Optional[float]:
    try:
        v = float(val.strip())
        return v if v > 0 else None
    except (ValueError, AttributeError):
        return None

def filetypes_input():
    exts = " ".join(f"*{e}" for e in sorted(INPUT_EXTS))
    return [("Semua gambar", exts), ("Semua file", "*.*")]

# Tooltip
# ---------------------------------------------------------------------------
class Tooltip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self.show)
        widget.bind("<Leave>", self.hide)

    def show(self, _):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tk.Label(tw, text=self.text, background="#fffde7", relief="solid",
                 borderwidth=1, font=("Segoe UI", 9), padx=6, pady=3).pack()

    def hide(self, _):
        if self.tip:
            self.tip.destroy()
            self.tip = None

# Aplikasi utama
# ---------------------------------------------------------------------------
class App(tk.Tk):
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
        try:
            self.iconphoto(True, ImageTk.PhotoImage(Image.open("monolight.png")))
        except Exception:
            pass

    # ------------------------------------------------------------------
    def _build_ui(self):
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

        log_frame = ttk.LabelFrame(self, text="Log", padding=6)
        log_frame.pack(fill="both", padx=10, pady=(4, 4))

        self.log = tk.Text(log_frame, height=6, font=("Courier New", 9),
                           state="disabled", wrap="word",
                           background="#f8f8f8", relief="flat")
        scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        self.log.tag_config("ok",  foreground="#1D9E75")
        self.log.tag_config("err", foreground="#E24B4A")
        self.log.tag_config("inf", foreground="#185FA5")

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=400)
        self.progress.pack(fill="x", padx=10, pady=(0, 8))

    # ------------------------------------------------------------------
    # Tab 1 — Konversi
    # ------------------------------------------------------------------
    def _build_single(self, parent, PAD):
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

        ttk.Label(f, text="Format output").grid(row=3, column=0, sticky="w", **PAD)
        cb = ttk.Combobox(f, textvariable=self.s_fmt, values=OUTPUT_FORMATS,
                          state="readonly", width=12)
        cb.grid(row=3, column=1, sticky="w", **PAD)
        cb.bind("<<ComboboxSelected>>", lambda e: self._update_dst_ext(self.s_dst, self.s_fmt))

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

    # ------------------------------------------------------------------
    # Tab 2 — Resize
    # ------------------------------------------------------------------
    def _build_resize(self, parent, PAD):
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

        ttk.Label(f, text="Kualitas").grid(row=9, column=0, sticky="w", **PAD)
        qf = ttk.Frame(f)
        qf.grid(row=9, column=1, sticky="ew", **PAD)
        ttk.Scale(qf, from_=1, to=100, variable=self.r_qual, orient="horizontal", length=180,
                  command=lambda v: self.r_qual.set(int(float(v)))).pack(side="left")
        ttk.Label(qf, textvariable=self.r_qual, width=3).pack(side="left", padx=4)

        ttk.Button(f, text="Resize Sekarang", command=self._run_resize
                   ).grid(row=10, column=0, columnspan=3, pady=(10, 4), ipadx=20)
        f.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Tab 3 — Batch
    # ------------------------------------------------------------------
    def _build_batch(self, parent, PAD):
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

        ttk.Label(f, text="Lebar (px)").grid(row=6, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_w, width=12).grid(row=6, column=1, sticky="w", **PAD)
        ttk.Label(f, text="Tinggi (px)").grid(row=7, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_h, width=12).grid(row=7, column=1, sticky="w", **PAD)
        ttk.Label(f, text="Skala (%)").grid(row=8, column=0, sticky="w", **PAD)
        ttk.Entry(f, textvariable=self.b_scale, width=12).grid(row=8, column=1, sticky="w", **PAD)

        ttk.Checkbutton(f, text="Masuk subfolder (recursive)", variable=self.b_rec
                        ).grid(row=9, column=0, columnspan=3, sticky="w", **PAD)

        ttk.Button(f, text="Mulai Batch Konversi", command=self._run_batch
                   ).grid(row=10, column=0, columnspan=3, pady=(10, 4), ipadx=20)
        f.columnconfigure(1, weight=1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _row(self, parent, row, label, var, cmd):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=10, pady=4)
        ttk.Entry(parent, textvariable=var, width=32).grid(row=row, column=1,
                                                            sticky="ew", padx=4, pady=4)
        ttk.Button(parent, text="Pilih...", command=cmd, width=8).grid(row=row, column=2,
                                                                         padx=4, pady=4)

    def _update_dst_ext(self, dst_var, fmt_var):
        dst = dst_var.get()
        if dst:
            new_ext = EXT_MAP.get(fmt_var.get(), Path(dst).suffix)
            dst_var.set(str(Path(dst).with_suffix(new_ext)))

    def _pick_src(self, src_var, dst_var, fmt_var):
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
        def _write():
            self.log.configure(state="normal")
            self.log.insert("end", msg + "\n", tag)
            self.log.see("end")
            self.log.configure(state="disabled")
        self.after(0, _write)

    def _set_progress(self, running: bool):
        def _toggle():
            if running:
                self.progress.start(12)
            else:
                self.progress.stop()
                self.progress["value"] = 0
        self.after(0, _toggle)

    @staticmethod
    def _mode_str(mode_label: str) -> str:
        return {
            "Proporsional (fit)": "fit",
            "Tepat (exact)":      "exact",
            "Thumbnail (crop)":   "thumbnail",
        }.get(mode_label, "fit")

    # ------------------------------------------------------------------
    # Runner — Konversi satu file
    # ------------------------------------------------------------------
    def _run_single(self):
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
                is_svg = Path(src).suffix.lower() == ".svg"
                if is_svg:
                    img = open_image(Path(src), svg_width=w, svg_height=h, svg_scale=scale)
                else:
                    img = open_image(Path(src))
                    if w or h or scale:
                        img = do_resize(img, width=w, height=h, scale=scale, mode=mode)
                ext   = EXT_MAP.get(fmt, Path(dst).suffix)
                dst_p = Path(dst).with_suffix(ext)
                save_image(img, dst_p, quality=qual, fmt_override=fmt)
                self._log(f"✓  {Path(src).name}  →  {dst_p.name}  {img.size}", "ok")
            except Exception as e:
                self._log(f"✗  {e}", "err")
                traceback.print_exc()
            finally:
                self._set_progress(False)

        threading.Thread(target=task, daemon=True).start()

    # ------------------------------------------------------------------
    # Runner — Resize saja
    # ------------------------------------------------------------------
    def _run_resize(self):
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
                is_svg = Path(src).suffix.lower() == ".svg"
                if is_svg:
                    img = open_image(Path(src), svg_width=w, svg_height=h, svg_scale=scale)
                else:
                    img = open_image(Path(src))
                    img = do_resize(img, width=w, height=h, scale=scale,
                                    max_w=maxw, max_h=maxh, mode=mode)
                save_image(img, Path(dst), quality=qual)
                self._log(f"✓  {Path(src).name}  →  {Path(dst).name}  {img.size}", "ok")
            except Exception as e:
                self._log(f"✗  {e}", "err")
            finally:
                self._set_progress(False)

        threading.Thread(target=task, daemon=True).start()

    # ------------------------------------------------------------------
    # Runner — Batch
    # ------------------------------------------------------------------
    def _run_batch(self):
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
            for f in files:
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
            self._log(f"Selesai: {ok_count} berhasil, {err_count} gagal.", "inf")
            self._set_progress(False)

        threading.Thread(target=task, daemon=True).start()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.mainloop()