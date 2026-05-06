# Guia completa - amaru_fo PDF TOOL

Pagina: <https://amarufo.github.io/PAGE-AIP/>
OCR/Tesseract recomendado: <https://github.com/UB-Mannheim/tesseract>

```text
Al iniciar, la herramienta muestra el arte de ascci.txt junto con amaru_fo y la pagina web.
```

## Instalacion facil en Windows

Para una persona sin conocimiento de Python:

1. Descargar la carpeta completa.
2. Extraer el ZIP si viene comprimida.
3. Hacer doble clic en `install_windows.bat`.
4. Aceptar los permisos que pida Windows.
5. Cuando pregunte por OCR, pulsar Enter para instalarlo o escribir `n` para omitirlo.
6. Abrir el acceso directo `amaru_fo PDF TOOL` que queda en el Escritorio.

Si Windows dice que no encuentra Python, instalarlo desde <https://www.python.org/downloads/> y marcar `Add Python to PATH`. Luego repetir el paso 3.

Si el instalador no logra instalar Tesseract automaticamente, descarga el instalador Windows de UB-Mannheim desde <https://github.com/UB-Mannheim/tesseract>.

## Instalacion facil en Linux

Para preparar la herramienta dentro de esta carpeta:

```bash
chmod +x install_linux.sh run_pdftool.sh
./install_linux.sh
```

Luego ejecuta:

```bash
./run_pdftool.sh
```

Si falta soporte de entornos virtuales en Debian/Ubuntu:

```bash
sudo apt install python3 python3-venv python3-pip
```

Para OCR en Debian/Ubuntu:

```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

## Menu interactivo

Ejecuta:

```powershell
run_pdftool.bat
```

En Linux:

```bash
./run_pdftool.sh
```

O, si ya esta instalado, abre el acceso directo del Escritorio.

El menu esta ordenado por categorias:

- Trabajo frecuente: numerar, firmar y previsualizar.
- Armar documentos: unir, dividir, extraer, insertar.
- Reparar y convertir: desbloquear, OCR/TXT.
- Editar y optimizar: rotar, eliminar, comprimir, extraer imagenes.
- Convertir: PDF a imagenes e imagenes a PDF.
- Seguridad: proteger con contrasena y editar metadatos.
- Ayuda: informacion del PDF y enlace web.

## Opcion recomendada

Usa la opcion `1 - stamp` para numerar y firmar en un solo paso.

```powershell
python pdftool.py stamp documento.pdf --signature firma.png -o documento_final.pdf --reverse --preview muestra.png
```

`--reverse` significa que la ultima pagina queda con `000001`, como en el script original `numerar_paginas.py`.

## Vista previa

Antes de tocar todo el PDF puedes generar una muestra PNG:

```powershell
python pdftool.py preview documento.pdf --signature firma.png -o muestra.png --reverse --number-corner tr --signature-corner br --signature-scale 1.2
```

## Esquinas

```text
 +------------------------------------------------+
 | TL                                      TR     |
 |                                                |
 |                 VISTA DE PAGINA                |
 |                                                |
 | BL                                      BR     |
 +------------------------------------------------+
```

- `tl`: arriba izquierda
- `tr`: arriba derecha
- `bl`: abajo izquierda
- `br`: abajo derecha

## Paginas

| Ejemplo | Significa |
| --- | --- |
| `1,3,5` | paginas sueltas |
| `2-7` | rango |
| `1,3-5,10-12` | mezcla |
| `all` | todas |
| `-5` | desde la primera hasta la 5 |
| `10-` | desde la 10 hasta el final |

## Comandos rapidos

```powershell
python pdftool.py merge a.pdf b.pdf -o unido.pdf
python pdftool.py split documento.pdf -o partes -n 10
python pdftool.py extract documento.pdf:1,3-5 -o seleccion.pdf
python pdftool.py insert --host base.pdf --guest anexo.pdf --after 5 -o resultado.pdf
python pdftool.py number documento.pdf -o numerado.pdf --corner tr --reverse
python pdftool.py sign documento.pdf --signature firma.png -o firmado.pdf --corner br --scale 1.2
python pdftool.py rotate documento.pdf -o rotado.pdf --degrees 90 --pages 1,3-5
python pdftool.py delete-pages documento.pdf --pages 2,5-7 -o limpio.pdf
python pdftool.py compress documento.pdf -o optimizado.pdf
python pdftool.py extract-images documento.pdf -o imagenes
python pdftool.py watermark documento.pdf --text "CONFIDENCIAL" -o marcado.pdf --opacity 0.16
python pdftool.py pdf-to-images documento.pdf -o paginas --pages 1-3 --dpi 200 --format png
python pdftool.py images-to-pdf foto1.png foto2.jpg -o desde_imagenes.pdf
python pdftool.py protect documento.pdf -o protegido.pdf --password "clave"
python pdftool.py metadata documento.pdf -o metadatos.pdf --title "Expediente" --author "amaru_fo"
python pdftool.py info documento.pdf
```

## Desbloquear PDF

Modo normal:

```powershell
python pdftool.py unlock protegido.pdf -o libre.pdf --password "clave"
```

Modo para PDFs firmados/certificados que siguen bloqueados:

```powershell
python pdftool.py unlock firmado.pdf -o libre.pdf --rebuild
```

`--rebuild` crea una copia visual nueva. Libera restricciones, pero elimina firmas digitales verificables y formularios interactivos.

## TXT y OCR

```powershell
python pdftool.py totxt documento.pdf -o documento.txt
python pdftool.py totxt escaneado.pdf -o escaneado.txt --ocr --lang spa
```

Para OCR instala tambien Tesseract. En Windows usa el instalador recomendado; en Linux usa el gestor de paquetes de tu distribucion.

Descarga recomendada para Windows:

```text
https://github.com/UB-Mannheim/tesseract
```

En Debian/Ubuntu:

```bash
sudo apt install tesseract-ocr tesseract-ocr-spa
```

## Herramientas nuevas

### Marca de agua

```powershell
python pdftool.py watermark documento.pdf --text "BORRADOR" -o borrador.pdf --opacity 0.20 --font-size 48 --rotate 0
```

### PDF a imagenes

```powershell
python pdftool.py pdf-to-images documento.pdf -o paginas --pages all --dpi 200 --format png
```

### Imagenes a PDF

```powershell
python pdftool.py images-to-pdf portada.png pagina2.jpg -o imagenes.pdf
```

### Proteger PDF

```powershell
python pdftool.py protect documento.pdf -o protegido.pdf --password "clave"
```

### Metadatos

```powershell
python pdftool.py metadata documento.pdf -o final.pdf --title "Informe" --author "amaru_fo" --keywords "pdf,oficina"
```

## Acceso directo

El instalador crea:

```text
Escritorio\amaru_fo PDF TOOL.lnk
```

La herramienta queda instalada en:

```text
%LOCALAPPDATA%\AmaruFoPdfTool
```

## Publicar en GitHub

Repositorio objetivo:

```text
git@github.com:amarufo/pdf_tool_tactical.git
```

Recomienda a los usuarios:

1. Descargar ZIP.
2. Extraer ZIP.
3. Abrir `install_windows.bat`.
4. Usar el acceso directo del Escritorio.
