"""
pdftool.py - Suite multifuncional para edicion de PDFs en CLI.

Herramienta estilo iLovePDF para Windows/PowerShell, con menu interactivo,
colores, ASCII art, acciones combinadas y salidas faciles de ubicar.

Uso rapido:
    python pdftool.py
    python pdftool.py --help
    python pdftool.py stamp documento.pdf --signature firma.png -o salida.pdf --preview muestra.png

Dependencias:
    pip install pymupdf rich
Opcionales:
    pip install pikepdf             # desbloqueo mas robusto
    pip install pytesseract pillow  # OCR para PDFs escaneados
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import sys
import time
import webbrowser
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("ERROR: falta PyMuPDF. Instala con:  pip install pymupdf")
    sys.exit(1)

try:
    from rich import box
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
    from rich.prompt import Confirm, IntPrompt, Prompt
    from rich.table import Table
    from rich.text import Text
except ImportError:
    print("ERROR: falta rich. Instala con:  pip install rich")
    sys.exit(1)

console = Console()

AUTHOR_NAME = "amaru_fo"
AUTHOR_PAGE = "https://amarufo.github.io/PAGE-AIP/"
TESSERACT_URL = "https://github.com/UB-Mannheim/tesseract"
ASCII_ART_FILE = Path(__file__).with_name("ascci.txt")

ANIMALITO = r"""
 /\_/\\
( o.o )   amaru_fo helper
 > ^ <
"""

ANIMALITO_TRABAJO = r"""
 /\_/\\    [ trabajando ]
( -.- )  . . .
 > ^ <
"""

ANIMALITO_LISTO = r"""
 /\_/\\    [ listo ]
( ^.^ )  PDF preparado
 > ^ <
"""

TOOLBOX_ART = r"""
    .------------------------------------------------.
    |  PDF  | unir | cortar | firmar | OCR | rotar  |
    '------------------------------------------------'
                CLI visual para usuarios de oficina
"""

STEPS_ART = r"""
    [1] Elige accion  ->  [2] Escoge archivos  ->  [3] Revisa muestra  ->  [4] Listo
"""

BANNER = r"""
                                __       
  __ _ _ __ ___  __ _ _ __ _   _  / _| ___  
 / _` | '_ ` _ \/ _` | '__| | | || |_ / _ \ 
| (_| | | | | | | (_| | |  | |_| ||  _| (_) |
 \__,_|_| |_| |_|\__,_|_|   \__, (_)|_|  \___/ 
                            |___/             
          <<< amaru_fo >>>
        PDF TOOL CLI - edicion visual y guiada
"""

CORNERS_ART = r"""
 +------------------------------------------------+
 | TL                                      TR     |
 |                                                |
 |                 VISTA DE PAGINA                |
 |                                                |
 | BL                                      BR     |
 +------------------------------------------------+
   tl = arriba izquierda     tr = arriba derecha
   bl = abajo izquierda      br = abajo derecha
"""

STAMP_ART = r"""
 +------------------------------------------------+
 |                                      000123    |  <- numero
 |                                                |
 |                                                |
 |                                                |
 |                         [ firma transparente ] |  <- firma
 +------------------------------------------------+
"""

CORNER_MAP = {
    "tl": "arriba izquierda",
    "tr": "arriba derecha",
    "bl": "abajo izquierda",
    "br": "abajo derecha",
}

FONT_SIZE_DEFAULT = 13
DEFAULT_MARGIN = 25
DEFAULT_SIGNATURE_WIDTH = 100
DEFAULT_SIGNATURE_HEIGHT = 40


def load_intro_art() -> str:
    if not ASCII_ART_FILE.exists():
        return BANNER
    for encoding in ("utf-8", "utf-8-sig", "cp1252"):
        try:
            art = ASCII_ART_FILE.read_text(encoding=encoding).strip()
            if art:
                return art
        except UnicodeDecodeError:
            continue
    return ASCII_ART_FILE.read_text(encoding="utf-8", errors="replace").strip() or BANNER


def banner() -> None:
    intro = Text(load_intro_art(), style="bold cyan")
    console.print(Panel.fit(intro, title=AUTHOR_NAME, subtitle=AUTHOR_PAGE, border_style="cyan"))
    console.print(Panel(TOOLBOX_ART + f"\nAutor: {AUTHOR_NAME}\nPagina: {AUTHOR_PAGE}", border_style="green"))


def ok(message: str) -> None:
    console.print(Panel(f"{ANIMALITO_LISTO}\n[bold green]+[/bold green] {message}", border_style="green"))


def warn(message: str) -> None:
    console.print(Panel(f"{ANIMALITO_TRABAJO}\n[bold yellow]![/bold yellow] {message}", border_style="yellow"))


def err(message: str) -> None:
    console.print(Panel(f"{ANIMALITO}\n[bold red]x[/bold red] {message}", border_style="red"))


def start_operation(title: str, detail: str | None = None) -> float:
    text = f"{ANIMALITO_TRABAJO}\n[bold cyan]{title}[/bold cyan]"
    if detail:
        text += f"\n{detail}"
    console.print(Panel(text, title="Progreso", border_style="cyan"))
    return time.perf_counter()


def finish_operation(title: str, started_at: float, output: Path | None = None) -> None:
    elapsed = time.perf_counter() - started_at
    lines = [ANIMALITO_LISTO, f"[bold green]{title}[/bold green]", f"Tiempo: {elapsed:.1f}s"]
    if output is not None:
        resolved = Path(output).resolve()
        lines.extend([
            f"Nombre: [cyan]{resolved.name}[/cyan]",
            f"Carpeta: [magenta]{resolved.parent}[/magenta]",
            f"Ruta: [yellow]{resolved}[/yellow]",
        ])
    lines.append(f"Pagina amaru_fo: [underline blue]{AUTHOR_PAGE}[/underline blue]")
    console.print(Panel("\n".join(lines), title="Resultado", border_style="green"))


def open_author_page() -> None:
    console.print(Panel(f"{ANIMALITO}\nAbriendo pagina de amaru_fo:\n[blue underline]{AUTHOR_PAGE}[/blue underline]", border_style="blue"))
    webbrowser.open(AUTHOR_PAGE)


def ensure_parent(path: Path) -> None:
    Path(path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)


def show_file(label: str, path: Path) -> None:
    resolved = Path(path).resolve()
    console.print(
        Panel.fit(
            f"{ANIMALITO_LISTO}\n[bold]{label}[/bold]\n"
            f"  Nombre  : [cyan]{resolved.name}[/cyan]\n"
            f"  Carpeta : [magenta]{resolved.parent}[/magenta]\n"
            f"  Ruta    : [yellow]{resolved}[/yellow]\n"
            f"  Web     : [blue underline]{AUTHOR_PAGE}[/blue underline]",
            border_style="green",
            box=box.ROUNDED,
        )
    )


def show_teaching_panel() -> None:
    console.print(Panel(ANIMALITO + "\n" + STEPS_ART, title="Ruta facil", border_style="green"))
    console.print(Panel(CORNERS_ART, title="Esquinas", border_style="magenta"))
    console.print(
        Panel(
            "[bold]Seleccion de paginas[/bold]\n"
            "  1,3,5         paginas sueltas\n"
            "  2-7           rango\n"
            "  1,3-5,10-12   mezcla\n"
            "  all / todas   todas\n"
            "  -5            desde la primera hasta la 5\n"
            "  10-           desde la 10 hasta el final",
            border_style="cyan",
        )
    )


def parse_pages(spec: str | None, total: int) -> list[int]:
    if spec is None:
        return list(range(total))
    spec = spec.strip().lower()
    if spec in ("", "all", "todas", "*"):
        return list(range(total))
    pages: list[int] = []
    for token in re.split(r"[,\s]+", spec):
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = 1 if start_text in ("", "first", "inicio") else int(start_text)
            end = total if end_text in ("", "end", "last", "fin") else int(end_text)
            if start < 1 or end > total or start > end:
                raise ValueError(f"Rango invalido '{token}' (total={total})")
            pages.extend(range(start - 1, end))
        else:
            page = int(token)
            if page < 1 or page > total:
                raise ValueError(f"Pagina fuera de rango: {page} (total={total})")
            pages.append(page - 1)
    return pages


def out_path(src: Path, suffix: str, ext: str = ".pdf") -> Path:
    src = Path(src)
    return src.with_name(f"{src.stem}{suffix}{ext}")


def ask_path(message: str, must_exist: bool = True, is_dir: bool = False) -> Path:
    while True:
        raw = Prompt.ask(f"[bold]{message}[/bold]")
        path = Path(raw.strip().strip('"').strip("'"))
        if must_exist and not path.exists():
            err(f"No existe: {path}")
            continue
        if must_exist and is_dir and not path.is_dir():
            err(f"No es una carpeta: {path}")
            continue
        return path


def ask_corner(default: str = "tr") -> str:
    console.print(Panel(CORNERS_ART, title="Elige una esquina", border_style="magenta"))
    return Prompt.ask("Esquina", choices=["tl", "tr", "bl", "br"], default=default)


def ask_float(message: str, default: float) -> float:
    while True:
        raw = Prompt.ask(message, default=str(default))
        try:
            return float(raw.replace(",", "."))
        except ValueError:
            err("Escribe un numero valido, por ejemplo 1.25")


def page_count(path: Path) -> int:
    doc = fitz.open(path)
    total = len(doc)
    doc.close()
    return total


def describe_numbering(total: int, reverse: bool, start: int, digits: int) -> Table:
    table = Table(title="Como quedara la numeracion", box=box.ROUNDED, border_style="cyan")
    table.add_column("Pagina fisica", style="cyan")
    table.add_column("Numero impreso", style="bold yellow")
    samples = [1]
    if total > 2:
        samples.append((total + 1) // 2)
    if total > 1:
        samples.append(total)
    for physical in samples:
        value = total - physical + 1 if reverse else start + physical - 1
        table.add_row(str(physical), f"{value:0{digits}d}")
    return table


def corner_xy(
    rect: fitz.Rect,
    corner: str,
    width: float,
    height: float,
    margin: float = DEFAULT_MARGIN,
    x: float | None = None,
    y: float | None = None,
) -> tuple[float, float]:
    if x is not None and y is not None:
        return x, y
    if corner == "tl":
        return margin, margin
    if corner == "tr":
        return rect.width - margin - width, margin
    if corner == "bl":
        return margin, rect.height - margin - height
    if corner == "br":
        return rect.width - margin - width, rect.height - margin - height
    raise ValueError(f"Esquina invalida: {corner!r}")


def add_number_to_page(
    page: fitz.Page,
    value: int,
    corner: str,
    digits: int,
    font_size: int,
    margin: float = DEFAULT_MARGIN,
    x: float | None = None,
    y: float | None = None,
) -> None:
    text = f"{value:0{digits}d}"
    text_width = fitz.get_text_length("0" * digits, fontname="helv", fontsize=font_size)
    text_height = float(font_size)
    px, py = corner_xy(page.rect, corner, text_width, text_height, margin, x, y)
    page.insert_text(
        (px, py + text_height * 0.85),
        text,
        fontsize=font_size,
        fontname="helv",
        color=(0, 0, 0),
    )


def add_signature_to_page(
    page: fitz.Page,
    signature_bytes: bytes,
    signature_xref: int,
    corner: str,
    width: float,
    height: float,
    scale: float,
    margin: float = DEFAULT_MARGIN,
    x: float | None = None,
    y: float | None = None,
) -> int:
    final_width = width * scale
    final_height = height * scale
    px, py = corner_xy(page.rect, corner, final_width, final_height, margin, x, y)
    rect = fitz.Rect(px, py, px + final_width, py + final_height)
    if signature_xref:
        page.insert_image(rect, xref=signature_xref, keep_proportion=True)
        return signature_xref
    return page.insert_image(rect, stream=signature_bytes, keep_proportion=True)


def render_stamp_preview(
    input_pdf: Path,
    output_png: Path,
    signature: Path | None,
    page_number: int,
    number_corner: str,
    signature_corner: str,
    reverse: bool,
    start: int,
    digits: int,
    font_size: int,
    signature_width: float,
    signature_height: float,
    signature_scale: float,
    number_x: float | None = None,
    number_y: float | None = None,
    signature_x: float | None = None,
    signature_y: float | None = None,
) -> None:
    src = fitz.open(input_pdf)
    total = len(src)
    if page_number < 1 or page_number > total:
        src.close()
        raise ValueError(f"Pagina de vista previa fuera de rango (1-{total})")
    preview = fitz.open()
    preview.insert_pdf(src, from_page=page_number - 1, to_page=page_number - 1)
    src.close()
    page = preview[0]
    value = total - page_number + 1 if reverse else start + page_number - 1
    add_number_to_page(page, value, number_corner, digits, font_size, x=number_x, y=number_y)
    if signature:
        add_signature_to_page(
            page,
            signature.read_bytes(),
            0,
            signature_corner,
            signature_width,
            signature_height,
            signature_scale,
            x=signature_x,
            y=signature_y,
        )
    pix = page.get_pixmap(dpi=160)
    ensure_parent(output_png)
    pix.save(output_png)
    preview.close()
    show_file("Vista previa PNG", output_png)


def save_pdf(doc: fitz.Document, output: Path, fast_overlay: bool = False) -> None:
    ensure_parent(output)
    kwargs = {"garbage": 1, "deflate": True}
    if fast_overlay:
        kwargs.update({"deflate_images": False, "deflate_fonts": False})
    doc.save(output, **kwargs)


def cmd_merge(inputs: list[Path], output: Path) -> None:
    out = fitz.open()
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(),
                  console=console) as progress:
        task = progress.add_task("Uniendo PDFs", total=len(inputs))
        for pdf in inputs:
            doc = fitz.open(pdf)
            out.insert_pdf(doc)
            doc.close()
            progress.advance(task)
    save_pdf(out, output)
    out.close()
    show_file("PDF unido", output)


def cmd_split(input_pdf: Path, output_dir: Path, every: int = 1) -> list[Path]:
    if every < 1:
        raise ValueError("--every debe ser 1 o mayor")
    output_dir.mkdir(parents=True, exist_ok=True)
    src = fitz.open(input_pdf)
    files: list[Path] = []
    total = len(src)
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task("Dividiendo", total=total)
        part = 0
        for start_page in range(0, total, every):
            end_page = min(start_page + every - 1, total - 1)
            part += 1
            new_doc = fitz.open()
            new_doc.insert_pdf(src, from_page=start_page, to_page=end_page)
            output = output_dir / f"{input_pdf.stem}_parte{part:03d}_p{start_page + 1}-{end_page + 1}.pdf"
            save_pdf(new_doc, output)
            new_doc.close()
            files.append(output)
            progress.advance(task, end_page - start_page + 1)
    src.close()
    ok(f"Generadas {len(files)} partes en {output_dir.resolve()}")
    for item in files[:12]:
        console.print(f"  - {item.name}")
    if len(files) > 12:
        console.print(f"  ... y {len(files) - 12} mas")
    return files


def cmd_extract(inputs: list[tuple[Path, str]], output: Path) -> None:
    out = fitz.open()
    summary: list[tuple[str, str, int]] = []
    for pdf, spec in inputs:
        doc = fitz.open(pdf)
        pages = parse_pages(spec, len(doc))
        for page_index in pages:
            out.insert_pdf(doc, from_page=page_index, to_page=page_index)
        summary.append((Path(pdf).name, spec, len(pages)))
        doc.close()
    save_pdf(out, output)
    out.close()
    table = Table(title="Paginas extraidas/combinadas", box=box.ROUNDED, border_style="cyan")
    table.add_column("Archivo", style="cyan")
    table.add_column("Seleccion", style="yellow")
    table.add_column("Paginas", justify="right", style="green")
    for name, spec, count in summary:
        table.add_row(name, spec, str(count))
    console.print(table)
    show_file("PDF resultante", output)


def cmd_insert(host: Path, guest: Path, after_page: int, guest_pages: str | None, output: Path) -> None:
    host_doc = fitz.open(host)
    guest_doc = fitz.open(guest)
    if after_page < 0 or after_page > len(host_doc):
        host_doc.close()
        guest_doc.close()
        raise ValueError(f"--after fuera de rango; {host.name} tiene {len(host_doc)} paginas")
    if guest_pages:
        selected = parse_pages(guest_pages, len(guest_doc))
        tmp = fitz.open()
        for page_index in selected:
            tmp.insert_pdf(guest_doc, from_page=page_index, to_page=page_index)
        guest_doc.close()
        guest_doc = tmp
    host_doc.insert_pdf(guest_doc, start_at=after_page)
    save_pdf(host_doc, output)
    host_doc.close()
    guest_doc.close()
    show_file("PDF con insercion", output)


def cmd_unlock(input_pdf: Path, output: Path, password: str | None, rebuild: bool = False) -> None:
    if rebuild:
        warn("Reconstruccion visual: elimina cifrado, restricciones, firmas digitales y formularios interactivos.")
        src = fitz.open(input_pdf)
        if src.is_encrypted and not src.authenticate(password or ""):
            src.close()
            raise RuntimeError("Con reconstruccion visual tambien se necesita la clave de apertura si el PDF la exige.")
        out = fitz.open()
        with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                      TextColumn("{task.completed}/{task.total}"), console=console) as progress:
            task = progress.add_task("Reconstruyendo paginas", total=len(src))
            for page_index in range(len(src)):
                page = src[page_index]
                new_page = out.new_page(width=page.rect.width, height=page.rect.height)
                new_page.show_pdf_page(page.rect, src, page_index)
                progress.advance(task)
        save_pdf(out, output)
        src.close()
        out.close()
        show_file("PDF reconstruido/desbloqueado", output)
        return

    try:
        pikepdf = __import__("pikepdf")
    except ImportError:
        pikepdf = None
    if pikepdf is not None:
        try:
            ensure_parent(output)
            with pikepdf.open(input_pdf, password=password or "", allow_overwriting_input=True) as pdf:
                pdf.save(output)
            show_file("PDF desbloqueado con pikepdf", output)
            return
        except Exception as exc:
            warn(f"pikepdf no pudo desbloquearlo: {exc}")
            warn("Probando guardado sin cifrado con PyMuPDF.")

    doc = fitz.open(input_pdf)
    if doc.is_encrypted and not doc.authenticate(password or ""):
        doc.close()
        raise RuntimeError("Contrasena incorrecta o PDF protegido sin clave conocida.")
    ensure_parent(output)
    doc.save(output, garbage=4, deflate=True, encryption=getattr(fitz, "PDF_ENCRYPT_NONE", 1))
    doc.close()
    show_file("PDF desbloqueado", output)
    warn("Si sigue bloqueado por firma/certificacion, repite con --rebuild.")


def cmd_to_txt(input_pdf: Path, output: Path, ocr: bool, lang: str = "spa") -> None:
    doc = fitz.open(input_pdf)
    total = len(doc)
    use_ocr = ocr
    parts: list[str] = []
    if not use_ocr:
        sample = "".join(str(doc[index].get_text("text")) for index in range(min(3, total)))
        if not sample.strip():
            warn("El PDF parece escaneado; se activara OCR.")
            use_ocr = True
    if use_ocr:
        try:
            pytesseract = __import__("pytesseract")
            Image = __import__("PIL.Image", fromlist=["Image"])
        except ImportError:
            doc.close()
            raise RuntimeError(f"Para OCR instala pytesseract/pillow y Tesseract para Windows: {TESSERACT_URL}")
        # Auto-detectar ruta de Tesseract en Windows (evita error de PATH)
        import os as _os
        _TESS_PATHS = [
            shutil.which("tesseract"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            _os.path.join(_os.environ.get("LOCALAPPDATA", ""), "Programs", "Tesseract-OCR", "tesseract.exe"),
        ]
        for _tp in _TESS_PATHS:
            if _tp and _os.path.exists(_tp):
                pytesseract.pytesseract.tesseract_cmd = _tp
                break
        if not _os.path.exists(getattr(pytesseract.pytesseract, "tesseract_cmd", "")):
            warn(f"No encuentro Tesseract. Instala la version Windows desde: {TESSERACT_URL}")
        # Configurar TESSDATA_PREFIX: preferir carpeta de usuario (~\tessdata) con spa incluido
        _user_tessdata = _os.path.join(_os.path.expanduser("~"), "tessdata")
        _sys_tessdata = _os.path.join(_os.path.dirname(pytesseract.pytesseract.tesseract_cmd), "tessdata")
        # Elegir la carpeta que tenga el archivo del idioma solicitado
        _chosen_tessdata = None
        for _td in [_user_tessdata, _sys_tessdata]:
            if _os.path.exists(_os.path.join(_td, f"{lang}.traineddata")):
                _chosen_tessdata = _td
                break
        if _chosen_tessdata is None:
            # Fallback a eng si el idioma no existe
            warn(f"Modelo OCR '{lang}' no encontrado. Usando 'eng'. Descarga '{lang}.traineddata' en: {_user_tessdata}")
            lang = "eng"
            _chosen_tessdata = _user_tessdata if _os.path.exists(_os.path.join(_user_tessdata, "eng.traineddata")) else _sys_tessdata
        _os.environ["TESSDATA_PREFIX"] = _chosen_tessdata

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task("Extrayendo texto" + (" con OCR" if use_ocr else ""), total=total)
        for index in range(len(doc)):
            page = doc[index]
            if use_ocr:
                pix = page.get_pixmap(dpi=300)
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(image, lang=lang)
            else:
                text = page.get_text()
            parts.append(f"\n===== Pagina {index + 1} =====\n{text}")
            progress.advance(task)
    doc.close()
    ensure_parent(output)
    output.write_text("".join(parts), encoding="utf-8")
    show_file("TXT generado", output)


def cmd_number(
    input_pdf: Path,
    output: Path,
    corner: str = "tr",
    digits: int = 6,
    reverse: bool = False,
    start: int = 1,
    font_size: int = FONT_SIZE_DEFAULT,
    x: float | None = None,
    y: float | None = None,
) -> None:
    doc = fitz.open(input_pdf)
    total = len(doc)
    console.print(describe_numbering(total, reverse, start, digits))
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task(f"Numerando en {CORNER_MAP[corner]}", total=total)
        for index in range(len(doc)):
            page = doc[index]
            value = total - index if reverse else start + index
            add_number_to_page(page, value, corner, digits, font_size, x=x, y=y)
            progress.advance(task)
    save_pdf(doc, output, fast_overlay=True)
    doc.close()
    show_file("PDF numerado", output)


def cmd_sign(
    input_pdf: Path,
    signature: Path,
    output: Path,
    corner: str = "br",
    width: float = DEFAULT_SIGNATURE_WIDTH,
    height: float = DEFAULT_SIGNATURE_HEIGHT,
    scale: float = 1.0,
    pages_spec: str | None = None,
    x: float | None = None,
    y: float | None = None,
) -> None:
    if not signature.exists():
        raise FileNotFoundError(f"No existe la firma: {signature}")
    signature_bytes = signature.read_bytes()
    doc = fitz.open(input_pdf)
    total = len(doc)
    target = set(parse_pages(pages_spec, total))
    signature_xref = 0
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task(f"Firmando en {CORNER_MAP[corner]}", total=total)
        for index in range(len(doc)):
            page = doc[index]
            if index in target:
                signature_xref = add_signature_to_page(
                    page, signature_bytes, signature_xref, corner, width, height, scale, x=x, y=y
                )
            progress.advance(task)
    save_pdf(doc, output, fast_overlay=True)
    doc.close()
    show_file("PDF firmado", output)


def cmd_stamp(
    input_pdf: Path,
    signature: Path,
    output: Path,
    number_corner: str = "tr",
    signature_corner: str = "br",
    digits: int = 6,
    reverse: bool = True,
    start: int = 1,
    font_size: int = FONT_SIZE_DEFAULT,
    signature_width: float = DEFAULT_SIGNATURE_WIDTH,
    signature_height: float = DEFAULT_SIGNATURE_HEIGHT,
    signature_scale: float = 1.0,
    signature_pages: str | None = None,
    preview: Path | None = None,
) -> None:
    if preview:
        render_stamp_preview(
            input_pdf, preview, signature, 1, number_corner, signature_corner,
            reverse, start, digits, font_size, signature_width, signature_height, signature_scale,
        )
    signature_bytes = signature.read_bytes()
    doc = fitz.open(input_pdf)
    total = len(doc)
    target = set(parse_pages(signature_pages, total))
    signature_xref = 0
    console.print(describe_numbering(total, reverse, start, digits))
    console.print(
        Panel(
            STAMP_ART
            + f"\nNumero: {CORNER_MAP[number_corner]} | Firma: {CORNER_MAP[signature_corner]} | Escala firma: {signature_scale}",
            title="Modo combinado: numerar + firmar",
            border_style="green",
        )
    )
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), TimeElapsedColumn(),
                  console=console) as progress:
        task = progress.add_task("Aplicando numero y firma", total=total)
        for index in range(len(doc)):
            page = doc[index]
            value = total - index if reverse else start + index
            add_number_to_page(page, value, number_corner, digits, font_size)
            if index in target:
                signature_xref = add_signature_to_page(
                    page, signature_bytes, signature_xref, signature_corner,
                    signature_width, signature_height, signature_scale,
                )
            progress.advance(task)
    save_pdf(doc, output, fast_overlay=True)
    doc.close()
    show_file("PDF numerado y firmado", output)


def cmd_rotate(input_pdf: Path, output: Path, degrees: int, pages_spec: str | None = None) -> None:
    if degrees % 90 != 0:
        raise ValueError("La rotacion debe ser multiplo de 90")
    doc = fitz.open(input_pdf)
    target = set(parse_pages(pages_spec, len(doc)))
    for index in range(len(doc)):
        page = doc[index]
        if index in target:
            page.set_rotation((page.rotation + degrees) % 360)
    save_pdf(doc, output)
    doc.close()
    show_file("PDF rotado", output)


def cmd_delete(input_pdf: Path, output: Path, pages_spec: str) -> None:
    doc = fitz.open(input_pdf)
    pages = sorted(set(parse_pages(pages_spec, len(doc))), reverse=True)
    if len(pages) >= len(doc):
        doc.close()
        raise ValueError("No se pueden borrar todas las paginas del PDF")
    for page_index in pages:
        doc.delete_page(page_index)
    save_pdf(doc, output)
    doc.close()
    show_file("PDF con paginas eliminadas", output)


def cmd_compress(input_pdf: Path, output: Path) -> None:
    before = input_pdf.stat().st_size
    doc = fitz.open(input_pdf)
    ensure_parent(output)
    doc.save(output, garbage=4, deflate=True, deflate_images=True, deflate_fonts=True, clean=True)
    doc.close()
    after = output.stat().st_size
    table = Table(title="Compresion/optimizacion", box=box.ROUNDED, border_style="cyan")
    table.add_column("Archivo", style="cyan")
    table.add_column("Tamano", justify="right", style="yellow")
    table.add_row("Original", f"{before / 1024 / 1024:.2f} MB")
    table.add_row("Salida", f"{after / 1024 / 1024:.2f} MB")
    console.print(table)
    show_file("PDF optimizado", output)


def cmd_extract_images(input_pdf: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(input_pdf)
    seen: set[int] = set()
    count = 0
    for page_number in range(len(doc)):
        for image_index, image in enumerate(doc.get_page_images(page_number, full=True), start=1):
            xref = image[0]
            if xref in seen:
                continue
            seen.add(xref)
            data = doc.extract_image(xref)
            extension = data.get("ext", "png")
            count += 1
            name = f"{input_pdf.stem}_p{page_number + 1:03d}_img{image_index:02d}.{extension}"
            (output_dir / name).write_bytes(data["image"])
    doc.close()
    ok(f"Imagenes extraidas: {count}")
    show_file("Carpeta de imagenes", output_dir)


def cmd_pdf_to_images(input_pdf: Path, output_dir: Path, pages_spec: str | None = None, dpi: int = 200, image_format: str = "png") -> list[Path]:
    if dpi < 72:
        raise ValueError("--dpi debe ser 72 o mayor")
    image_format = image_format.lower().lstrip(".")
    if image_format not in ("png", "jpg", "jpeg"):
        raise ValueError("Formato de imagen permitido: png, jpg o jpeg")
    output_dir.mkdir(parents=True, exist_ok=True)
    doc = fitz.open(input_pdf)
    pages = parse_pages(pages_spec, len(doc))
    files: list[Path] = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task("Exportando paginas a imagen", total=len(pages))
        for page_index in pages:
            page = doc[page_index]
            pix = page.get_pixmap(dpi=dpi, alpha=False)
            extension = "jpg" if image_format == "jpeg" else image_format
            output = output_dir / f"{input_pdf.stem}_p{page_index + 1:03d}.{extension}"
            pix.save(output)
            files.append(output)
            progress.advance(task)
    doc.close()
    ok(f"Paginas exportadas: {len(files)}")
    show_file("Carpeta de imagenes renderizadas", output_dir)
    return files


def cmd_images_to_pdf(inputs: list[Path], output: Path) -> None:
    if not inputs:
        raise ValueError("Debes indicar al menos una imagen")
    out = fitz.open()
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task("Convirtiendo imagenes a PDF", total=len(inputs))
        for image_path in inputs:
            if not image_path.exists():
                raise FileNotFoundError(f"No existe la imagen: {image_path}")
            image_doc = fitz.open(image_path)
            pdf_bytes = image_doc.convert_to_pdf()
            image_doc.close()
            pdf_doc = fitz.open("pdf", pdf_bytes)
            out.insert_pdf(pdf_doc)
            pdf_doc.close()
            progress.advance(task)
    save_pdf(out, output)
    out.close()
    show_file("PDF creado desde imagenes", output)


def cmd_watermark(
    input_pdf: Path,
    output: Path,
    text: str,
    pages_spec: str | None = None,
    font_size: int = 42,
    opacity: float = 0.16,
    rotate: int = 0,
) -> None:
    if not text.strip():
        raise ValueError("El texto de marca de agua no puede estar vacio")
    if rotate not in (0, 90, 180, 270):
        raise ValueError("La rotacion de texto debe ser 0, 90, 180 o 270")
    if opacity < 0 or opacity > 1:
        raise ValueError("La opacidad debe estar entre 0 y 1")
    doc = fitz.open(input_pdf)
    target = set(parse_pages(pages_spec, len(doc)))
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TextColumn("{task.completed}/{task.total}"), console=console) as progress:
        task = progress.add_task("Aplicando marca de agua", total=len(doc))
        for index in range(len(doc)):
            page = doc[index]
            if index in target:
                rect = page.rect
                box_height = max(font_size * 2, 80)
                box = fitz.Rect(0, rect.height / 2 - box_height / 2, rect.width, rect.height / 2 + box_height / 2)
                kwargs = {
                    "fontsize": font_size,
                    "fontname": "helv",
                    "color": (0.45, 0.45, 0.45),
                    "align": fitz.TEXT_ALIGN_CENTER,
                    "rotate": rotate,
                    "overlay": True,
                }
                try:
                    page.insert_textbox(box, text, fill_opacity=opacity, **kwargs)
                except TypeError:
                    page.insert_textbox(box, text, **kwargs)
            progress.advance(task)
    save_pdf(doc, output, fast_overlay=True)
    doc.close()
    show_file("PDF con marca de agua", output)


def cmd_protect(input_pdf: Path, output: Path, user_password: str, owner_password: str | None = None) -> None:
    if not user_password:
        raise ValueError("Debes indicar una contrasena de apertura")
    doc = fitz.open(input_pdf)
    ensure_parent(output)
    doc.save(
        output,
        garbage=4,
        deflate=True,
        encryption=getattr(fitz, "PDF_ENCRYPT_AES_256", 5),
        owner_pw=owner_password or user_password,
        user_pw=user_password,
        permissions=getattr(fitz, "PDF_PERM_PRINT", 4),
    )
    doc.close()
    show_file("PDF protegido con contrasena", output)


def cmd_metadata(
    input_pdf: Path,
    output: Path,
    title: str | None = None,
    author: str | None = None,
    subject: str | None = None,
    keywords: str | None = None,
) -> None:
    doc = fitz.open(input_pdf)
    metadata = dict(doc.metadata or {})
    updates = {
        "title": title,
        "author": author,
        "subject": subject,
        "keywords": keywords,
    }
    for key, value in updates.items():
        if value is not None:
            metadata[key] = value
    doc.set_metadata(metadata)
    save_pdf(doc, output)
    doc.close()
    show_file("PDF con metadatos actualizados", output)


def cmd_info(input_pdf: Path) -> None:
    doc = fitz.open(input_pdf)
    table = Table(title=f"Informacion de {input_pdf.name}", box=box.ROUNDED, border_style="cyan")
    table.add_column("Dato", style="cyan")
    table.add_column("Valor", style="yellow")
    table.add_row("Ruta", str(input_pdf.resolve()))
    table.add_row("Paginas", str(len(doc)))
    table.add_row("Encriptado", "si" if doc.is_encrypted else "no")
    table.add_row("Tamano", f"{input_pdf.stat().st_size / 1024 / 1024:.2f} MB")
    metadata = doc.metadata or {}
    for key in ("title", "author", "subject", "creator", "producer"):
        if metadata.get(key):
            table.add_row(key, metadata[key])
    doc.close()
    console.print(table)


MENU = [
    ("Trabajo frecuente", "1", "stamp", "Numerar + firmar en una sola accion, con vista previa"),
    ("Trabajo frecuente", "2", "preview", "Generar muestra PNG de numero/firma"),
    ("Trabajo frecuente", "3", "number", "Solo numerar paginas"),
    ("Trabajo frecuente", "4", "sign", "Solo insertar firma"),
    ("Armar documentos", "5", "merge", "Unir PDFs"),
    ("Armar documentos", "6", "split", "Dividir PDF"),
    ("Armar documentos", "7", "extract", "Extraer o reordenar paginas"),
    ("Armar documentos", "8", "insert", "Insertar PDF dentro de otro"),
    ("Reparar y convertir", "9", "unlock", "Desbloquear o reconstruir PDF bloqueado"),
    ("Reparar y convertir", "10", "totxt", "Convertir PDF a TXT / OCR"),
    ("Editar y optimizar", "11", "rotate", "Rotar paginas"),
    ("Editar y optimizar", "12", "delete", "Eliminar paginas"),
    ("Editar y optimizar", "13", "compress", "Optimizar/comprimir PDF"),
    ("Editar y optimizar", "14", "images", "Extraer imagenes"),
    ("Editar y optimizar", "15", "watermark", "Agregar marca de agua de texto"),
    ("Convertir", "16", "pdf-images", "Convertir paginas de PDF a imagenes"),
    ("Convertir", "17", "images-pdf", "Crear PDF desde imagenes"),
    ("Seguridad", "18", "protect", "Proteger PDF con contrasena"),
    ("Seguridad", "19", "metadata", "Editar metadatos del PDF"),
    ("Ayuda", "20", "info", "Ver informacion del PDF"),
    ("Ayuda", "w", "web", "Abrir pagina de amaru_fo"),
    ("Ayuda", "h", "ayuda", "Ver guia visual"),
    ("Ayuda", "0", "salir", "Salir"),
]


def show_menu() -> None:
    console.print(Panel(
        ANIMALITO + "\n[bold]amaru_fo PDF TOOL[/bold]\n"
        "Recomendado: empieza con la opcion 1 para numerar + firmar.\n"
        f"Pagina: [blue underline]{AUTHOR_PAGE}[/blue underline]",
        border_style="cyan",
    ))
    table = Table(title="Menu principal por categorias", box=box.ROUNDED, border_style="cyan")
    table.add_column("Categoria", style="magenta")
    table.add_column("Opcion", justify="center", style="bold yellow")
    table.add_column("Accion", style="bold green")
    table.add_column("Para que sirve", style="white")
    last_category = None
    for category, key, command, description in MENU:
        table.add_row(category if category != last_category else "", key, command, description)
        last_category = category
    console.print(table)


def ask_numbering_options(total: int) -> tuple[bool, int, int]:
    digits = IntPrompt.ask("Digitos del numero", default=6)
    direction = Prompt.ask("Orden de numeracion", choices=["inicio-fin", "fin-inicio"], default="fin-inicio")
    reverse = direction == "fin-inicio"
    start = 1 if reverse else IntPrompt.ask("Numero inicial", default=1)
    console.print(describe_numbering(total, reverse, start, digits))
    return reverse, start, digits


def interactive_stamp() -> None:
    console.print(Panel(STAMP_ART, title="Asistente recomendado: numerar + firmar", border_style="green"))
    src = ask_path("PDF a trabajar")
    signature = ask_path("Imagen de firma (PNG transparente recomendado)")
    total = page_count(src)
    reverse, start, digits = ask_numbering_options(total)
    number_corner = ask_corner("tr")
    signature_corner = ask_corner("br")
    scale = ask_float("Escala de firma (1.0 = tamano base 100x40 pt)", 1.0)
    signature_pages = Prompt.ask("Paginas donde va la firma", default="all")
    signature_pages = None if signature_pages.lower() in ("all", "todas", "*") else signature_pages
    preview = out_path(src, "_muestra", ".png")
    if Confirm.ask("Generar vista previa PNG antes de aplicar", default=True):
        render_stamp_preview(
            src, preview, signature, 1, number_corner, signature_corner, reverse,
            start, digits, FONT_SIZE_DEFAULT, DEFAULT_SIGNATURE_WIDTH,
            DEFAULT_SIGNATURE_HEIGHT, scale,
        )
    output = Path(Prompt.ask("Archivo PDF final", default=str(out_path(src, "_numerado_firmado"))))
    console.print(
        Panel(
            f"PDF: [cyan]{src.name}[/cyan]\n"
            f"Numero: [yellow]{CORNER_MAP[number_corner]}[/yellow] | orden: {'fin-inicio' if reverse else 'inicio-fin'}\n"
            f"Firma: [yellow]{CORNER_MAP[signature_corner]}[/yellow] | escala: {scale}\n"
            f"Salida: [green]{output}[/green]",
            title="Revisar antes de ejecutar",
            border_style="yellow",
        )
    )
    if Confirm.ask("Aplicar ahora", default=True):
        cmd_stamp(src, signature, output, number_corner, signature_corner, digits, reverse, start, signature_scale=scale, signature_pages=signature_pages)


def interactive_number() -> None:
    src = ask_path("PDF a numerar")
    total = page_count(src)
    reverse, start, digits = ask_numbering_options(total)
    corner = ask_corner("tr")
    output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_numerado"))))
    cmd_number(src, output, corner=corner, digits=digits, reverse=reverse, start=start)


def interactive_sign() -> None:
    src = ask_path("PDF a firmar")
    signature = ask_path("Imagen de firma")
    corner = ask_corner("br")
    scale = ask_float("Escala de firma", 1.0)
    pages = Prompt.ask("Paginas a firmar", default="all")
    pages = None if pages.lower() in ("all", "todas", "*") else pages
    preview = out_path(src, "_muestra_firma", ".png")
    if Confirm.ask("Generar vista previa PNG", default=True):
        render_stamp_preview(src, preview, signature, 1, "tr", corner, False, 1, 6, FONT_SIZE_DEFAULT, DEFAULT_SIGNATURE_WIDTH, DEFAULT_SIGNATURE_HEIGHT, scale)
    output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_firmado"))))
    cmd_sign(src, signature, output, corner=corner, scale=scale, pages_spec=pages)


def interactive() -> None:
    banner()
    while True:
        show_menu()
        try:
            choice = Prompt.ask("[bold cyan]Elige opcion[/bold cyan]", choices=[item[1] for item in MENU], default="1")
        except EOFError:
            warn("No se recibio una opcion. Se cierra el menu de forma segura.")
            return
        try:
            if choice == "0":
                console.print("[bold cyan]Listo. Hasta luego.[/bold cyan]")
                return
            if choice == "h":
                show_teaching_panel()
            elif choice == "w":
                open_author_page()
            elif choice == "1":
                interactive_stamp()
            elif choice == "2":
                src = ask_path("PDF para la vista previa")
                signature = ask_path("Firma para la vista previa")
                total = page_count(src)
                reverse, start, digits = ask_numbering_options(total)
                number_corner = ask_corner("tr")
                signature_corner = ask_corner("br")
                scale = ask_float("Escala de firma", 1.0)
                output = Path(Prompt.ask("PNG de salida", default=str(out_path(src, "_muestra", ".png"))))
                render_stamp_preview(src, output, signature, 1, number_corner, signature_corner, reverse, start, digits, FONT_SIZE_DEFAULT, DEFAULT_SIGNATURE_WIDTH, DEFAULT_SIGNATURE_HEIGHT, scale)
            elif choice == "3":
                interactive_number()
            elif choice == "4":
                interactive_sign()
            elif choice == "5":
                count = IntPrompt.ask("Cuantos PDFs quieres unir")
                inputs = [ask_path(f"PDF {index + 1}") for index in range(count)]
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(inputs[0], "_unido"))))
                cmd_merge(inputs, output)
            elif choice == "6":
                src = ask_path("PDF a dividir")
                every = IntPrompt.ask("Cada cuantas paginas", default=1)
                outdir = Path(Prompt.ask("Carpeta de salida", default=str(src.parent / f"{src.stem}_partes")))
                cmd_split(src, outdir, every)
            elif choice == "7":
                show_teaching_panel()
                count = IntPrompt.ask("Cuantos PDFs origen", default=1)
                specs = []
                for index in range(count):
                    pdf = ask_path(f"PDF {index + 1}")
                    pages = Prompt.ask(f"Paginas de {pdf.name}", default="all")
                    specs.append((pdf, pages))
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(specs[0][0], "_extraido"))))
                cmd_extract(specs, output)
            elif choice == "8":
                show_teaching_panel()
                host = ask_path("PDF anfitrion")
                guest = ask_path("PDF a insertar")
                after = IntPrompt.ask("Insertar despues de la pagina (0 = inicio)", default=0)
                pages = Prompt.ask("Paginas del PDF insertado", default="all")
                pages = None if pages.lower() in ("all", "todas", "*") else pages
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(host, "_con_inserto"))))
                cmd_insert(host, guest, after, pages, output)
            elif choice == "9":
                src = ask_path("PDF bloqueado")
                password = Prompt.ask("Contrasena (vacio si no aplica)", default="", password=True)
                rebuild = Confirm.ask("Usar reconstruccion visual para PDFs firmados/certificados", default=True)
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_desbloqueado"))))
                cmd_unlock(src, output, password or None, rebuild=rebuild)
            elif choice == "10":
                src = ask_path("PDF a convertir")
                ocr = Confirm.ask("Forzar OCR", default=False)
                lang = Prompt.ask("Idioma OCR", default="spa") if ocr else "spa"
                output = Path(Prompt.ask("TXT de salida", default=str(out_path(src, "", ".txt"))))
                cmd_to_txt(src, output, ocr=ocr, lang=lang)
            elif choice == "11":
                src = ask_path("PDF a rotar")
                degrees = IntPrompt.ask("Grados (90, 180, 270, -90)", default=90)
                pages = Prompt.ask("Paginas", default="all")
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_rotado"))))
                cmd_rotate(src, output, degrees, None if pages.lower() in ("all", "todas", "*") else pages)
            elif choice == "12":
                src = ask_path("PDF a recortar/eliminar paginas")
                show_teaching_panel()
                pages = Prompt.ask("Paginas a eliminar")
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_sin_paginas"))))
                cmd_delete(src, output, pages)
            elif choice == "13":
                src = ask_path("PDF a optimizar")
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_optimizado"))))
                cmd_compress(src, output)
            elif choice == "14":
                src = ask_path("PDF origen")
                outdir = Path(Prompt.ask("Carpeta de imagenes", default=str(src.parent / f"{src.stem}_imagenes")))
                cmd_extract_images(src, outdir)
            elif choice == "15":
                src = ask_path("PDF a marcar")
                text = Prompt.ask("Texto de marca de agua", default="CONFIDENCIAL")
                pages = Prompt.ask("Paginas", default="all")
                size = IntPrompt.ask("Tamano del texto", default=42)
                opacity = ask_float("Opacidad (0.10 suave, 0.35 visible)", 0.16)
                rotate = IntPrompt.ask("Rotacion (0, 90, 180, 270)", default=0)
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_marca_agua"))))
                cmd_watermark(src, output, text, None if pages.lower() in ("all", "todas", "*") else pages, size, opacity, rotate)
            elif choice == "16":
                src = ask_path("PDF a convertir en imagenes")
                pages = Prompt.ask("Paginas", default="all")
                dpi = IntPrompt.ask("Calidad DPI", default=200)
                fmt = Prompt.ask("Formato", choices=["png", "jpg", "jpeg"], default="png")
                outdir = Path(Prompt.ask("Carpeta de salida", default=str(src.parent / f"{src.stem}_paginas")))
                cmd_pdf_to_images(src, outdir, None if pages.lower() in ("all", "todas", "*") else pages, dpi, fmt)
            elif choice == "17":
                count = IntPrompt.ask("Cuantas imagenes quieres convertir", default=1)
                inputs = [ask_path(f"Imagen {index + 1}") for index in range(count)]
                output = Path(Prompt.ask("PDF de salida", default=str(inputs[0].with_name(f"{inputs[0].stem}_imagenes.pdf"))))
                cmd_images_to_pdf(inputs, output)
            elif choice == "18":
                src = ask_path("PDF a proteger")
                password = Prompt.ask("Contrasena para abrir", password=True)
                owner = Prompt.ask("Contrasena de propietario (opcional)", default="", password=True)
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_protegido"))))
                cmd_protect(src, output, password, owner or None)
            elif choice == "19":
                src = ask_path("PDF para editar metadatos")
                title = Prompt.ask("Titulo", default="")
                author = Prompt.ask("Autor", default=AUTHOR_NAME)
                subject = Prompt.ask("Asunto", default="")
                keywords = Prompt.ask("Palabras clave", default="")
                output = Path(Prompt.ask("Archivo de salida", default=str(out_path(src, "_metadatos"))))
                cmd_metadata(src, output, title or None, author or None, subject or None, keywords or None)
            elif choice == "20":
                cmd_info(ask_path("PDF a inspeccionar"))
        except KeyboardInterrupt:
            warn("Operacion cancelada.")
        except Exception as exc:
            err(f"{type(exc).__name__}: {exc}")
        console.print()


def parse_extract_specs(specs: list[str]) -> list[tuple[Path, str]]:
    parsed: list[tuple[Path, str]] = []
    for spec in specs:
        if ":" not in spec:
            raise SystemExit(f"Formato invalido '{spec}'. Usa archivo.pdf:1,3-5")
        path_part, pages = spec.rsplit(":", 1)
        parsed.append((Path(path_part), pages))
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdftool",
        description="Suite CLI amaru_fo para editar PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sin argumentos abre el menu interactivo guiado.",
    )
    sub = parser.add_subparsers(dest="cmd")

    stamp = sub.add_parser("stamp", help="Numerar y firmar en una sola accion.")
    stamp.add_argument("input", type=Path)
    stamp.add_argument("--signature", type=Path, required=True)
    stamp.add_argument("-o", "--output", type=Path, required=True)
    stamp.add_argument("--number-corner", choices=list(CORNER_MAP), default="tr")
    stamp.add_argument("--signature-corner", choices=list(CORNER_MAP), default="br")
    stamp.add_argument("--digits", type=int, default=6)
    stamp.add_argument("--reverse", action="store_true", default=False, help="Ultima pagina = 000001.")
    stamp.add_argument("--start", type=int, default=1)
    stamp.add_argument("--font-size", type=int, default=FONT_SIZE_DEFAULT)
    stamp.add_argument("--signature-width", type=float, default=DEFAULT_SIGNATURE_WIDTH)
    stamp.add_argument("--signature-height", type=float, default=DEFAULT_SIGNATURE_HEIGHT)
    stamp.add_argument("--signature-scale", type=float, default=1.0)
    stamp.add_argument("--signature-pages", default=None)
    stamp.add_argument("--preview", type=Path, default=None, help="Genera PNG de muestra antes de guardar el PDF.")

    preview = sub.add_parser("preview", help="Crear vista previa PNG de numero/firma.")
    preview.add_argument("input", type=Path)
    preview.add_argument("--signature", type=Path, required=True)
    preview.add_argument("-o", "--output", type=Path, required=True)
    preview.add_argument("--page", type=int, default=1)
    preview.add_argument("--number-corner", choices=list(CORNER_MAP), default="tr")
    preview.add_argument("--signature-corner", choices=list(CORNER_MAP), default="br")
    preview.add_argument("--reverse", action="store_true")
    preview.add_argument("--start", type=int, default=1)
    preview.add_argument("--digits", type=int, default=6)
    preview.add_argument("--font-size", type=int, default=FONT_SIZE_DEFAULT)
    preview.add_argument("--signature-width", type=float, default=DEFAULT_SIGNATURE_WIDTH)
    preview.add_argument("--signature-height", type=float, default=DEFAULT_SIGNATURE_HEIGHT)
    preview.add_argument("--signature-scale", type=float, default=1.0)

    merge = sub.add_parser("merge", help="Unir varios PDFs.")
    merge.add_argument("inputs", nargs="+", type=Path)
    merge.add_argument("-o", "--output", type=Path, required=True)

    split = sub.add_parser("split", help="Dividir PDF cada N paginas.")
    split.add_argument("input", type=Path)
    split.add_argument("-o", "--output-dir", type=Path, required=True)
    split.add_argument("-n", "--every", type=int, default=1)

    extract = sub.add_parser("extract", help='Extraer paginas: "archivo.pdf:1,3-5".')
    extract.add_argument("specs", nargs="+")
    extract.add_argument("-o", "--output", type=Path, required=True)

    insert = sub.add_parser("insert", help="Insertar PDF dentro de otro.")
    insert.add_argument("--host", type=Path, required=True)
    insert.add_argument("--guest", type=Path, required=True)
    insert.add_argument("--after", type=int, default=0)
    insert.add_argument("--pages", default=None)
    insert.add_argument("-o", "--output", type=Path, required=True)

    number = sub.add_parser("number", help="Numerar paginas.")
    number.add_argument("input", type=Path)
    number.add_argument("-o", "--output", type=Path, required=True)
    number.add_argument("--corner", choices=list(CORNER_MAP), default="tr")
    number.add_argument("--digits", type=int, default=6)
    number.add_argument("--reverse", action="store_true")
    number.add_argument("--start", type=int, default=1)
    number.add_argument("--font-size", type=int, default=FONT_SIZE_DEFAULT)
    number.add_argument("--x", type=float, default=None)
    number.add_argument("--y", type=float, default=None)

    sign = sub.add_parser("sign", help="Insertar firma/imagen.")
    sign.add_argument("input", type=Path)
    sign.add_argument("--signature", type=Path, required=True)
    sign.add_argument("-o", "--output", type=Path, required=True)
    sign.add_argument("--corner", choices=list(CORNER_MAP), default="br")
    sign.add_argument("--width", type=float, default=DEFAULT_SIGNATURE_WIDTH)
    sign.add_argument("--height", type=float, default=DEFAULT_SIGNATURE_HEIGHT)
    sign.add_argument("--scale", type=float, default=1.0)
    sign.add_argument("--pages", default=None)
    sign.add_argument("--x", type=float, default=None)
    sign.add_argument("--y", type=float, default=None)

    unlock = sub.add_parser("unlock", help="Desbloquear PDF; usa --rebuild para firmados/certificados.")
    unlock.add_argument("input", type=Path)
    unlock.add_argument("-o", "--output", type=Path, required=True)
    unlock.add_argument("--password", default=None)
    unlock.add_argument("--rebuild", action="store_true")

    totxt = sub.add_parser("totxt", help="Convertir PDF a TXT, con OCR opcional.")
    totxt.add_argument("input", type=Path)
    totxt.add_argument("-o", "--output", type=Path, required=True)
    totxt.add_argument("--ocr", action="store_true")
    totxt.add_argument("--lang", default="spa")

    rotate = sub.add_parser("rotate", help="Rotar paginas.")
    rotate.add_argument("input", type=Path)
    rotate.add_argument("-o", "--output", type=Path, required=True)
    rotate.add_argument("--degrees", type=int, required=True)
    rotate.add_argument("--pages", default=None)

    delete = sub.add_parser("delete-pages", help="Eliminar paginas.")
    delete.add_argument("input", type=Path)
    delete.add_argument("--pages", required=True)
    delete.add_argument("-o", "--output", type=Path, required=True)

    compress = sub.add_parser("compress", help="Optimizar/comprimir PDF.")
    compress.add_argument("input", type=Path)
    compress.add_argument("-o", "--output", type=Path, required=True)

    images = sub.add_parser("extract-images", help="Extraer imagenes embebidas.")
    images.add_argument("input", type=Path)
    images.add_argument("-o", "--output-dir", type=Path, required=True)

    pdf_images = sub.add_parser("pdf-to-images", help="Renderizar paginas del PDF como PNG/JPG.")
    pdf_images.add_argument("input", type=Path)
    pdf_images.add_argument("-o", "--output-dir", type=Path, required=True)
    pdf_images.add_argument("--pages", default=None)
    pdf_images.add_argument("--dpi", type=int, default=200)
    pdf_images.add_argument("--format", choices=["png", "jpg", "jpeg"], default="png")

    images_pdf = sub.add_parser("images-to-pdf", help="Crear un PDF desde imagenes.")
    images_pdf.add_argument("inputs", nargs="+", type=Path)
    images_pdf.add_argument("-o", "--output", type=Path, required=True)

    watermark = sub.add_parser("watermark", help="Agregar marca de agua de texto.")
    watermark.add_argument("input", type=Path)
    watermark.add_argument("--text", required=True)
    watermark.add_argument("-o", "--output", type=Path, required=True)
    watermark.add_argument("--pages", default=None)
    watermark.add_argument("--font-size", type=int, default=42)
    watermark.add_argument("--opacity", type=float, default=0.16)
    watermark.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0)

    protect = sub.add_parser("protect", help="Proteger PDF con contrasena de apertura.")
    protect.add_argument("input", type=Path)
    protect.add_argument("-o", "--output", type=Path, required=True)
    protect.add_argument("--password", required=True)
    protect.add_argument("--owner-password", default=None)

    metadata = sub.add_parser("metadata", help="Actualizar metadatos del PDF.")
    metadata.add_argument("input", type=Path)
    metadata.add_argument("-o", "--output", type=Path, required=True)
    metadata.add_argument("--title", default=None)
    metadata.add_argument("--author", default=None)
    metadata.add_argument("--subject", default=None)
    metadata.add_argument("--keywords", default=None)

    info_cmd = sub.add_parser("info", help="Ver informacion de un PDF.")
    info_cmd.add_argument("input", type=Path)

    sub.add_parser("menu", help="Abrir menu interactivo.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.cmd or args.cmd == "menu":
        interactive()
        return 0

    banner()
    started_at = start_operation(f"Ejecutando accion: {args.cmd}", "El programa esta modificando o revisando tu PDF.")
    try:
        if args.cmd == "stamp":
            cmd_stamp(
                args.input, args.signature, args.output, args.number_corner,
                args.signature_corner, args.digits, args.reverse, args.start,
                args.font_size, args.signature_width, args.signature_height,
                args.signature_scale, args.signature_pages, args.preview,
            )
        elif args.cmd == "preview":
            render_stamp_preview(
                args.input, args.output, args.signature, args.page, args.number_corner,
                args.signature_corner, args.reverse, args.start, args.digits,
                args.font_size, args.signature_width, args.signature_height,
                args.signature_scale,
            )
        elif args.cmd == "merge":
            cmd_merge(args.inputs, args.output)
        elif args.cmd == "split":
            cmd_split(args.input, args.output_dir, args.every)
        elif args.cmd == "extract":
            cmd_extract(parse_extract_specs(args.specs), args.output)
        elif args.cmd == "insert":
            cmd_insert(args.host, args.guest, args.after, args.pages, args.output)
        elif args.cmd == "number":
            cmd_number(args.input, args.output, args.corner, args.digits, args.reverse, args.start, args.font_size, args.x, args.y)
        elif args.cmd == "sign":
            cmd_sign(args.input, args.signature, args.output, args.corner, args.width, args.height, args.scale, args.pages, args.x, args.y)
        elif args.cmd == "unlock":
            cmd_unlock(args.input, args.output, args.password, args.rebuild)
        elif args.cmd == "totxt":
            cmd_to_txt(args.input, args.output, args.ocr, args.lang)
        elif args.cmd == "rotate":
            cmd_rotate(args.input, args.output, args.degrees, args.pages)
        elif args.cmd == "delete-pages":
            cmd_delete(args.input, args.output, args.pages)
        elif args.cmd == "compress":
            cmd_compress(args.input, args.output)
        elif args.cmd == "extract-images":
            cmd_extract_images(args.input, args.output_dir)
        elif args.cmd == "pdf-to-images":
            cmd_pdf_to_images(args.input, args.output_dir, args.pages, args.dpi, args.format)
        elif args.cmd == "images-to-pdf":
            cmd_images_to_pdf(args.inputs, args.output)
        elif args.cmd == "watermark":
            cmd_watermark(args.input, args.output, args.text, args.pages, args.font_size, args.opacity, args.rotate)
        elif args.cmd == "protect":
            cmd_protect(args.input, args.output, args.password, args.owner_password)
        elif args.cmd == "metadata":
            cmd_metadata(args.input, args.output, args.title, args.author, args.subject, args.keywords)
        elif args.cmd == "info":
            cmd_info(args.input)
        finish_operation("Peticion terminada correctamente", started_at)
    except KeyboardInterrupt:
        warn("Cancelado.")
        return 130
    except Exception as exc:
        err(f"{type(exc).__name__}: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
