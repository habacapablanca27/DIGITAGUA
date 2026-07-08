# generar_ficha_pdf.py
# Genera un PDF por punto, replicando el diseño de la ficha modelo
# (Ficha_Modelo_Valle_de_Valdebezana.xlsx): escudo + cabecera del
# ayuntamiento, logo SOMACyL, caja de "Situación", caja de "Contador",
# dos fotos (Inmueble/Arqueta) y bloque "A RELLENAR EN FASE DE OBRA".

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor, black, white

AZUL = HexColor("#4472C4")
GRIS_BORDE = HexColor("#000000")

ASSETS = os.path.join(os.path.dirname(__file__), "assets")
ESCUDO = os.path.join(ASSETS, "escudo.png")
SOMACYL = os.path.join(ASSETS, "somacyl.png")


def _si_no(v):
    return "Sí" if v else "No"


def generar_ficha_pdf(punto, ruta_salida, municipio="", nucleo="", provincia=""):
    c = canvas.Canvas(ruta_salida, pagesize=A4)
    w, h = A4
    margen = 12 * mm
    x0, y_top = margen, h - margen
    ancho = w - 2 * margen

    y = y_top

    # ── CABECERA ──
    alto_cab = 28 * mm
    c.rect(x0, y - alto_cab, ancho, alto_cab, stroke=1, fill=0)
    if os.path.exists(ESCUDO):
        c.drawImage(ESCUDO, x0 + 2 * mm, y - alto_cab + 2 * mm, width=24 * mm,
                    height=24 * mm, preserveAspectRatio=True, mask="auto")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(x0 + 30 * mm, y - 9 * mm, f"AYUNTAMIENTO DE {municipio.upper()}")
    c.setFont("Helvetica", 10)
    c.drawString(x0 + 30 * mm, y - 15 * mm, nucleo.upper())
    c.drawString(x0 + 30 * mm, y - 20 * mm, provincia.upper())
    if os.path.exists(SOMACYL):
        c.drawImage(SOMACYL, x0 + ancho - 45 * mm, y - alto_cab + 5 * mm,
                    width=40 * mm, height=18 * mm, preserveAspectRatio=True, mask="auto")
    y -= alto_cab

    # ── FILA Nº FIJO / DIRECCIÓN / TIPO EDIFICACIÓN ──
    fila_h = 14 * mm
    col1, col2, col3 = 25 * mm, ancho - 25 * mm - 45 * mm, 45 * mm
    _celda_titulo_valor(c, x0, y, col1, fila_h, "Nº FIJO", punto.get("NFijo", ""))
    _celda_titulo_valor(c, x0 + col1, y, col2, fila_h, "DIRECCIÓN - Nº POLICÍA", punto.get("Direccion", ""))
    _celda_titulo_valor(c, x0 + col1 + col2, y, col3, fila_h, "TIPO DE EDIFICACIÓN", punto.get("TipEdifica", ""))
    y -= fila_h + 3 * mm

    # ── BLOQUE 1: Situación (foto) + columna de datos ──
    bloque1_h = 55 * mm
    foto_w = ancho * 0.42
    datos_w = ancho - foto_w
    _caja_foto(c, x0, y - bloque1_h, foto_w, bloque1_h, "Situación", punto.get("FotoSituacion"))

    filas_dcha = [
        ("Exterior", _si_no(punto.get("Exterior"))),
        ("n° Módulo Radio", punto.get("ModRadio", "")),
        ("Válvula de acometida", _si_no(punto.get("ValAcometi"))),
        ("Tipo de uso consumo", punto.get("TipUsoComu", "")),
        ("Coordenadas GPS", punto.get("CoordGPS", "")),
        ("Código QR", ""),
        ("Individual", _si_no(punto.get("Individual"))),
        ("Alojamiento", punto.get("Alojamiento", "")),
    ]
    _columna_pares(c, x0 + foto_w, y, datos_w, bloque1_h, filas_dcha, cols=2)
    y -= bloque1_h + 3 * mm

    # ── BLOQUE 2: Contador (foto) + Llave/Calibre/Diámetros, Lectura/Fecha, Marca/Observaciones ──
    bloque2_h = 40 * mm
    _caja_foto(c, x0, y - bloque2_h, foto_w, bloque2_h, "Contador", punto.get("FotoContador"))

    dx = x0 + foto_w
    dw = datos_w
    fh = bloque2_h / 3
    # Llave de contador | Calibre | Diámetros
    w3 = dw / 3
    _celda_titulo_valor(c, dx, y, w3, fh, "Llave de contador", _si_no(punto.get("LlaveContador")))
    _celda_titulo_valor(c, dx + w3, y, w3, fh, "Calibre", punto.get("Calibre", ""))
    _celda_titulo_valor(c, dx + 2 * w3, y, w3, fh, "Diámetros", punto.get("Diametros", ""))
    # Lectura | Fecha
    _celda_titulo_valor(c, dx, y - fh, dw / 2, fh, "Lectura", punto.get("Lectura", ""))
    _celda_titulo_valor(c, dx + dw / 2, y - fh, dw / 2, fh, "Fecha", punto.get("FecLectura", ""))
    # Marca/Modelo | Observaciones (con notas añadidas de campos sin hueco propio)
    obs = punto.get("Observaciones", "") or ""
    extra = []
    if punto.get("UbicarExte"):
        extra.append("Ubicar exterior")
    if punto.get("CambioTapa"):
        extra.append("Cambio de tapa")
    if punto.get("SeBorra"):
        extra.append("Se borra")
    if extra:
        obs = (obs + "  |  " if obs else "") + ", ".join(extra)
    _celda_titulo_valor(c, dx, y - 2 * fh, dw / 2, fh, "Marca/Modelo", punto.get("MarcaModel", ""))
    _celda_titulo_valor(c, dx + dw / 2, y - 2 * fh, dw / 2, fh, "Observaciones", obs, wrap=True)
    y -= bloque2_h + 3 * mm

    # ── BLOQUE 3: dos fotos (Inmueble / Arqueta) ──
    bloque3_h = 55 * mm
    mitad = ancho / 2
    _caja_foto(c, x0, y - bloque3_h, mitad - 1.5 * mm, bloque3_h, "Inmueble", punto.get("FotoInmueble"))
    _caja_foto(c, x0 + mitad + 1.5 * mm, y - bloque3_h, mitad - 1.5 * mm, bloque3_h, "Arqueta", punto.get("FotoArqueta"))
    y -= bloque3_h + 4 * mm

    # ── BLOQUE FASE DE OBRA ──
    fo_h = 24 * mm
    c.setFont("Helvetica-Bold", 8.5)
    c.drawCentredString(x0 + ancho / 2, y - 4 * mm, "A RELLENAR EN FASE DE OBRA")
    c.rect(x0, y - fo_h, ancho, fo_h, stroke=1, fill=0)
    c.line(x0, y - 6 * mm, x0 + ancho, y - 6 * mm)
    colw = ancho / 4
    etiquetas_fo = ["Nº Serie contador existente / Fecha instalación",
                    "Lectura contador a sustituir", "Nº Serie contador sustitución", "Observaciones"]
    for i, et in enumerate(etiquetas_fo):
        cx = x0 + i * colw
        if i > 0:
            c.line(cx, y - fo_h, cx, y - 6 * mm)
        c.setFont("Helvetica-Bold", 6.5)
        _texto_ajustado(c, et, cx + 1 * mm, y - 8.5 * mm, colw - 2 * mm, 6.5)

    c.showPage()
    c.save()


def _celda_titulo_valor(c, x, y_top, w, h, titulo, valor, wrap=False):
    th = min(h * 0.5, 5.5 * mm)
    c.setFillColor(AZUL)
    c.rect(x, y_top - th, w, th, stroke=1, fill=1)
    c.setFillColor(white)
    tam_titulo = 7.5 if h < 8 * mm else 8
    c.setFont("Helvetica-Bold", tam_titulo)
    c.drawCentredString(x + w / 2, y_top - th / 2 - tam_titulo * 0.35, titulo)

    c.setFillColor(black)
    c.setStrokeColor(black)
    area_valor_h = h - th
    c.rect(x, y_top - h, w, area_valor_h, stroke=1, fill=0)
    c.setFont("Helvetica", 8)
    valor = str(valor) if valor is not None else ""
    y_inicio_valor = y_top - th - min(3.2 * mm, area_valor_h - 1)
    if wrap:
        _texto_ajustado(c, valor, x + 1.5 * mm, y_inicio_valor, w - 3 * mm, 8,
                        y_min=y_top - h + 1 * mm)
    else:
        c.drawString(x + 1.5 * mm, y_inicio_valor, valor[:60])


def _columna_pares(c, x, y_top, w, h, filas, cols=2):
    """Filas tipo (etiqueta, valor) apiladas, cada una con su propia altura."""
    fh = h / len(filas)
    for i, (etq, val) in enumerate(filas):
        fy = y_top - i * fh
        _celda_titulo_valor(c, x, fy, w, fh, etq, val)


def _caja_foto(c, x, y, w, h, etiqueta, ruta_foto):
    c.setFillColor(AZUL)
    c.rect(x, y + h - 6 * mm, w, 6 * mm, stroke=1, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(x + w / 2, y + h - 4.2 * mm, etiqueta)
    c.setFillColor(black)
    c.rect(x, y, w, h - 6 * mm, stroke=1, fill=0)
    if ruta_foto and os.path.exists(ruta_foto):
        try:
            c.drawImage(ruta_foto, x + 1 * mm, y + 1 * mm, width=w - 2 * mm,
                        height=h - 8 * mm, preserveAspectRatio=True, anchor="c", mask="auto")
        except Exception:
            c.setFont("Helvetica-Oblique", 7)
            c.drawCentredString(x + w / 2, y + h / 2, "(no se pudo cargar la foto)")
    else:
        c.setFont("Helvetica-Oblique", 7)
        c.setFillColor(HexColor("#999999"))
        c.drawCentredString(x + w / 2, y + h / 2, "Sin foto")
        c.setFillColor(black)


def _texto_ajustado(c, texto, x, y, max_w, size, y_min=None):
    c.setFont("Helvetica", size)
    palabras = texto.split()
    linea = ""
    ly = y
    for p in palabras:
        prueba = (linea + " " + p).strip()
        if c.stringWidth(prueba, "Helvetica", size) <= max_w:
            linea = prueba
        else:
            if y_min is not None and ly < y_min:
                break
            c.drawString(x, ly, linea)
            ly -= size * 1.15
            linea = p
    if linea and (y_min is None or ly >= y_min):
        c.drawString(x, ly, linea)


def generar_todas_las_fichas(puntos, carpeta_salida, municipio="", nucleo="", provincia=""):
    os.makedirs(carpeta_salida, exist_ok=True)
    rutas = []
    for p in puntos:
        nombre = f"Ficha_{p.get('NFijo') or p.get('_id')}.pdf".replace("/", "-")
        ruta = os.path.join(carpeta_salida, nombre)
        generar_ficha_pdf(p, ruta, municipio=municipio, nucleo=nucleo, provincia=provincia)
        rutas.append(ruta)
    return rutas
