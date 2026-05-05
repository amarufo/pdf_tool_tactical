# amaru_fo PDF TOOL Tactical

Suite CLI visual para editar PDFs en Windows. Pensada para usuarios de oficina: abrir, elegir opcion, seleccionar archivos y obtener el PDF final.

Pagina del autor: <https://amarufo.github.io/PAGE-AIP/>
OCR/Tesseract recomendado: <https://github.com/UB-Mannheim/tesseract>

```text
El arranque muestra el arte incluido en ascci.txt, el nombre amaru_fo y la web del autor.
```

## Para usuarios sin experiencia en Python

1. Descarga esta carpeta completa.
2. Abre la carpeta.
3. Haz doble clic en `install_windows.bat`.
4. Acepta los permisos si Windows los pide.
5. Cuando pregunte por OCR, pulsa Enter para instalarlo o escribe `n` para omitirlo.
6. Abre el acceso directo del Escritorio llamado `amaru_fo PDF TOOL`.

Si el instalador no encuentra Python, intentara instalarlo con `winget`. Si eso tampoco funciona, instala Python manualmente desde <https://www.python.org/downloads/> y marca la opcion `Add Python to PATH`.

Para OCR, el instalador intenta usar `winget` con Tesseract de UB-Mannheim. Si no puede instalarlo automaticamente, abre la pagina oficial para descargarlo:

<https://github.com/UB-Mannheim/tesseract>

## Uso normal

Ejecuta el acceso directo del Escritorio y elige una opcion del menu.

La opcion recomendada es:

```text
1 - Numerar + firmar en una sola accion, con vista previa
```

El programa te preguntara:

- PDF a trabajar.
- Imagen de firma.
- Orden de numeracion: inicio-fin o fin-inicio.
- Esquina del numero.
- Esquina de la firma.
- Escala de firma.
- Si quieres generar una vista previa PNG antes de aplicar.

Consejo: cuando te pida una ruta, puedes arrastrar el PDF o la imagen hacia la ventana y soltarlo.

## Archivos incluidos

| Archivo | Para que sirve |
| --- | --- |
| `install_windows.bat` | Instalador de doble clic para usuarios basicos |
| `install_windows.ps1` | Instalador real en PowerShell |
| `run_pdftool.bat` | Abre la herramienta desde esta carpeta |
| `pdftool.py` | Programa principal |
| `ascci.txt` | Arte introductorio mostrado al iniciar |
| `requirements.txt` | Dependencias obligatorias |
| `requirements-optional.txt` | Dependencias opcionales para OCR/desbloqueo avanzado |
| `audit_pdftool.py` | Auditoria rapida de funcionamiento |
| `LEEME_PRIMERO.txt` | Instrucciones simples |
| `PDFTOOL.md` | Guia completa de comandos |

## Funciones

- Numerar y firmar PDFs en una sola accion.
- Crear vista previa PNG.
- Unir PDFs.
- Dividir PDFs.
- Extraer o reordenar paginas.
- Insertar un PDF dentro de otro.
- Desbloquear o reconstruir PDFs bloqueados.
- Convertir PDF a TXT/OCR.
- Rotar paginas.
- Eliminar paginas.
- Optimizar/comprimir.
- Extraer imagenes.
- Agregar marca de agua de texto.
- Exportar paginas de PDF a PNG/JPG.
- Crear PDF desde imagenes.
- Proteger PDF con contrasena.
- Editar metadatos.
- Ver informacion del PDF.

## Instalacion opcional de OCR y desbloqueo avanzado

Despues de instalar, abre PowerShell y ejecuta:

```powershell
cd "$env:LOCALAPPDATA\AmaruFoPdfTool"
.\.venv\Scripts\python.exe -m pip install -r requirements-optional.txt
```

Para OCR tambien instala Tesseract para Windows.

Descarga recomendada: <https://github.com/UB-Mannheim/tesseract>

## Auditoria rapida

Despues de instalar dependencias, puedes ejecutar una prueba completa con archivos temporales:

```powershell
python audit_pdftool.py
```

La auditoria crea un PDF de muestra y valida numeracion, marca de agua, metadatos, exportacion a imagenes, creacion de PDF desde imagenes y proteccion con contrasena.

## Publicar en GitHub

Repositorio objetivo:

```text
git@github.com:amarufo/pdf_tool_tactical.git
```

Indica a los usuarios que descarguen el ZIP del repositorio, lo extraigan y ejecuten `install_windows.bat`.
