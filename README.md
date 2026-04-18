# Image Resolver

A comprehensive GUI application for quick image format conversion and resizing using Python and tkinter.

## Features

- **Format Conversion**: Convert between 16+ image formats (PNG, JPEG, WEBP, TIFF, BMP, GIF, ICO, ICNS, JPEG2000, TGA, PCX, PPM, SGI, AVIF, QOI, DDS)
- **Image Resizing**: Scale images with multiple modes (proportional, exact, thumbnail/crop)
- **SVG & PDF Support**: Direct conversion from SVG and PDF files
- **Batch Processing**: Process multiple files at once with recursive folder support
- **Quality Control**: Adjustable compression quality for lossy formats
- **User-Friendly GUI**: Built with tkinter (cross-platform, no external dependencies for UI)
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Application Tabs

1. **Konversi** - Convert single image to different format with optional resize
2. **Resize** - Advanced resize options (scale %, max dimensions, multiple resize modes)
3. **Batch** - Process multiple images from a folder with consistent settings

## Requirements

- Python 3.7+
- tkinter (usually comes with Python)
- Pillow
- cairosvg
- pymupdf

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/ImageResolver.git
cd ImageResolver
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Or manually:
```bash
pip install Pillow cairosvg pymupdf
```

## Quick Start

1. Run the application:
```bash
python main.py
```

2. Choose a tab based on your needs:
   - **Konversi**: Single image conversion
   - **Resize**: Resize with advanced options
   - **Batch**: Process multiple images

3. Select input file/folder, set options, and click the button

## Usage

### Tab 1: Konversi (Conversion)
- Convert a single image to a different format
- Optional: Resize while converting
- Adjustable quality for JPEG/WEBP/AVIF
- Auto-generates output filename

### Tab 2: Resize
- Resize with multiple modes:
  - **Proporsional (fit)**: Maintain aspect ratio
  - **Tepat (exact)**: Force exact dimensions
  - **Thumbnail (crop)**: Crop to fill dimensions
- Scale by percentage
- Set maximum width/height constraints

### Tab 3: Batch
- Process multiple images from a folder
- Recursive option to process subfolders
- Consistent format and quality across all images
- Detailed success/failure log

## Project Structure

```
ImageResolver/
├── main.py                      # Entry point aplikasi
├── src/                         # Source code package
│   ├── __init__.py              # Package initializer
│   ├── app.py                   # Main GUI application class
│   ├── image_processor.py       # Core image processing functions
│   ├── constants.py             # Format, extension, dan konfigurasi
│   └── ui_components.py         # GUI utilities (Tooltip, helpers)
├── depricated/                  # Legacy files
│   └── ImageResolver.py         # (deprecated - gunakan main.py)
├── requirements.txt             # Python dependencies
├── LICENSE                      # MIT License
├── README.md                    # This file
├── monolight.png                # Application icon
└── .gitignore                   # Git ignore rules
```

### Module Descriptions

| Module | Purpose |
|--------|---------|
| **main.py** | Entry point aplikasi. Validasi tkinter dan Pillow dependencies, kemudian menjalankan GUI. |
| **src/app.py** | Kelas `App` (tkinter.Tk) yang handle seluruh UI dan aplikasi logic. Terdiri dari 3 tab: Konversi, Resize, Batch. |
| **src/image_processor.py** | Fungsi core untuk image processing: `open_image()` (buka SVG/PDF/gambar), `save_image()` (simpan dengan konversi mode), dan `do_resize()` (resize dengan berbagai mode). |
| **src/constants.py** | Konstanta global: format output, mapping ekstensi file, set ekstensi input, mode konversi, dan konfigurasi lainnya. |
| **src/ui_components.py** | Komponen dan utility reusable: kelas `Tooltip` untuk hover hints, dan fungsi parser (`int_or_none`, `float_or_none`, `filetypes_input`). |

## Building Executable (Optional)

To create a standalone executable using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --icon=monolight.png --name="Image Resolver" --distpath="./dist" main.py
```

The executable will be available in `./dist/` folder.

## Development

### Project Architecture

The project follows a modular architecture:
- **main.py**: Bootstrap and dependency validation
- **src/app.py**: UI layer (tkinter GUI)
- **src/image_processor.py**: Business logic (image operations)
- **src/constants.py**: Configuration and constants
- **src/ui_components.py**: Reusable UI components

### Adding New Formats

1. Add format to `OUTPUT_FORMATS` in `src/constants.py`
2. Add extension mapping to `EXT_MAP` if needed
3. Add mode conversion logic in `save_image()` if needed

### Running Tests

To create tests, import modules from `src/`:
```python
from src.image_processor import open_image, do_resize
from src.constants import OUTPUT_FORMATS
```

## Supported Formats

### Input Formats
- **Raster**: JPG, PNG, WEBP, AVIF, QOI, TIFF, BMP, GIF, ICO, ICNS, JP2, TGA, PCX, PPM, SGI, DDS, PSD, XBM, XPM, DCX, MSP, EPS
- **Vector**: SVG
- **Document**: PDF

### Output Formats (16+)
PNG, JPEG, WEBP, TIFF, BMP, GIF, ICO, ICNS, JPEG2000, TGA, PCX, PPM, SGI, AVIF, QOI, DDS

## License

This project is licensed under the MIT License
