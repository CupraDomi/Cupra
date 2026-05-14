"""
Generador de facturas PDF para albaranes cerrados.
Librería: reportlab (ya incluida en requirements.txt).
"""
import os
from io import BytesIO
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, Image,
)
from reportlab.pdfgen import canvas as pdf_canvas

# ── Constantes ────────────────────────────────────────────────────────────────

NAVY   = HexColor('#1a2e5a')
LIGHT  = HexColor('#e8ecf4')
WHITE  = white
BLACK  = black
GREY   = HexColor('#666666')

PAGE_W, PAGE_H = A4
MARGIN = 2 * cm
CONTENT_W = PAGE_W - 2 * MARGIN

LOGO_PATH = os.path.join(os.path.dirname(__file__), 'static', 'img', 'sim_logo.png')

COMPANY = {
    'name':    'Soluciones Integrales de Maquinaria Sur S.L.',
    'cif':     'B14933931',
    'address': 'C/ Gabriel Ramos Bejarano, 122 A-B\nPolígono Industrial Las Quemadas\n14014 Córdoba',
    'phone':   '957 740 004',
}

STRINGS = {
    'es': {
        'invoice':       'FACTURA',
        'inv_num':       'Nº Factura',
        'issue_date':    'Fecha de emisión',
        'albaran_ref':   'Ref. albarán',
        'client_title':  'DATOS DEL CLIENTE',
        'desc':          'Descripción',
        'date_start':    'Fecha inicio',
        'date_end':      'Fecha fin',
        'duration':      'Duración',
        'unit_price':    'Precio unitario',
        'amount':        'Importe',
        'rental':        'Alquiler de maquinaria',
        'location_lbl':  'Obra / ubicación',
        'tax_base':      'Base imponible',
        'vat':           'IVA (21 %)',
        'total':         'TOTAL',
        'footer':        'Gracias por su confianza',
        'bank':          '[AÑADIR DATOS BANCARIOS]',
        'days':          'días',
        'weeks':         'semanas',
        'months':        'meses',
        'fixed':         'precio cerrado',
        'page':          'Página',
        'of':            'de',
    },
    'en': {
        'invoice':       'INVOICE',
        'inv_num':       'Invoice No.',
        'issue_date':    'Issue date',
        'albaran_ref':   'Delivery note ref.',
        'client_title':  'BILL TO',
        'desc':          'Description',
        'date_start':    'Start date',
        'date_end':      'End date',
        'duration':      'Duration',
        'unit_price':    'Unit price',
        'amount':        'Amount',
        'rental':        'Machinery rental',
        'location_lbl':  'Site / location',
        'tax_base':      'Taxable base',
        'vat':           'VAT (21 %)',
        'total':         'TOTAL',
        'footer':        'Thank you for your business',
        'bank':          '[ADD BANK DETAILS]',
        'days':          'days',
        'weeks':         'weeks',
        'months':        'months',
        'fixed':         'fixed price',
        'page':          'Page',
        'of':            'of',
    },
}

# ── Estilos de párrafo ────────────────────────────────────────────────────────

def _styles():
    return {
        'company_name': ParagraphStyle('cn',
            fontName='Helvetica-Bold', fontSize=9, textColor=NAVY, leading=12),
        'company_detail': ParagraphStyle('cd',
            fontName='Helvetica', fontSize=7.5, textColor=GREY, leading=10),
        'invoice_title': ParagraphStyle('it',
            fontName='Helvetica-Bold', fontSize=28, textColor=NAVY,
            alignment=TA_RIGHT, leading=32),
        'inv_label': ParagraphStyle('il',
            fontName='Helvetica-Bold', fontSize=8, textColor=GREY,
            alignment=TA_RIGHT, leading=11),
        'inv_value': ParagraphStyle('iv',
            fontName='Helvetica', fontSize=8, textColor=BLACK,
            alignment=TA_RIGHT, leading=11),
        'inv_num_value': ParagraphStyle('inv',
            fontName='Helvetica-Bold', fontSize=10, textColor=NAVY,
            alignment=TA_RIGHT, leading=13),
        'section_title': ParagraphStyle('st',
            fontName='Helvetica-Bold', fontSize=7.5, textColor=NAVY,
            spaceAfter=3, leading=10),
        'client_name': ParagraphStyle('cln',
            fontName='Helvetica-Bold', fontSize=9, textColor=BLACK, leading=12),
        'client_detail': ParagraphStyle('cld',
            fontName='Helvetica', fontSize=8, textColor=GREY, leading=11),
        'table_header': ParagraphStyle('th',
            fontName='Helvetica-Bold', fontSize=8, textColor=WHITE, leading=10),
        'table_cell': ParagraphStyle('tc',
            fontName='Helvetica', fontSize=8, textColor=BLACK, leading=11),
        'table_cell_r': ParagraphStyle('tcr',
            fontName='Helvetica', fontSize=8, textColor=BLACK,
            alignment=TA_RIGHT, leading=11),
        'table_sub': ParagraphStyle('ts',
            fontName='Helvetica', fontSize=7.5, textColor=GREY,
            leftIndent=8, leading=10),
        'total_label': ParagraphStyle('tl',
            fontName='Helvetica', fontSize=9, textColor=BLACK,
            alignment=TA_RIGHT, leading=13),
        'total_label_bold': ParagraphStyle('tlb',
            fontName='Helvetica-Bold', fontSize=10, textColor=NAVY,
            alignment=TA_RIGHT, leading=14),
        'total_value': ParagraphStyle('tv',
            fontName='Helvetica', fontSize=9, textColor=BLACK,
            alignment=TA_RIGHT, leading=13),
        'total_value_bold': ParagraphStyle('tvb',
            fontName='Helvetica-Bold', fontSize=10, textColor=NAVY,
            alignment=TA_RIGHT, leading=14),
        'footer': ParagraphStyle('ft',
            fontName='Helvetica', fontSize=8, textColor=GREY,
            alignment=TA_CENTER, leading=11),
        'bank': ParagraphStyle('bk',
            fontName='Helvetica-Bold', fontSize=8, textColor=NAVY,
            alignment=TA_CENTER, leading=11, spaceBefore=4),
    }


# ── Canvas con número de página ───────────────────────────────────────────────

class _NumberedCanvas(pdf_canvas.Canvas):
    def __init__(self, *args, **kwargs):
        pdf_canvas.Canvas.__init__(self, *args, **kwargs)
        self._saved_page_states = []
        self._lang = 'es'

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            if total > 1:
                t = STRINGS.get(self._lang, STRINGS['es'])
                self.setFont('Helvetica', 7.5)
                self.setFillColor(GREY)
                self.drawRightString(
                    PAGE_W - MARGIN, 1.2 * cm,
                    f"{t['page']} {self._pageNumber} {t['of']} {total}",
                )
            pdf_canvas.Canvas.showPage(self)
        pdf_canvas.Canvas.save(self)


# ── Secciones del PDF ─────────────────────────────────────────────────────────

def _header(note, s, t):
    """Tabla de cabecera: logo+empresa (izq) | FACTURA+detalles (dcha)."""
    left_items = []

    if os.path.exists(LOGO_PATH):
        left_items.append(Image(LOGO_PATH, width=4.5 * cm, height=2 * cm,
                                kind='proportional'))
        left_items.append(Spacer(1, 0.2 * cm))

    left_items.append(Paragraph(COMPANY['name'], s['company_name']))
    left_items.append(Paragraph(f"CIF: {COMPANY['cif']}", s['company_detail']))
    for line in COMPANY['address'].split('\n'):
        left_items.append(Paragraph(line, s['company_detail']))
    left_items.append(Paragraph(f"Tel: {COMPANY['phone']}", s['company_detail']))

    # Columna derecha
    issue_date = (note.invoice_generated_at or note.created_at).strftime('%d/%m/%Y')
    right_items = [
        Paragraph(t['invoice'], s['invoice_title']),
        Spacer(1, 0.15 * cm),
        Paragraph(f"<b>{t['inv_num']}:</b>", s['inv_label']),
        Paragraph(note.invoice_number, s['inv_num_value']),
        Spacer(1, 0.1 * cm),
        Paragraph(f"<b>{t['issue_date']}:</b>", s['inv_label']),
        Paragraph(issue_date, s['inv_value']),
        Spacer(1, 0.05 * cm),
        Paragraph(f"<b>{t['albaran_ref']}:</b>", s['inv_label']),
        Paragraph(note.albaran_number, s['inv_value']),
    ]

    # Construir la tabla con dos celdas
    def _cell(items):
        tbl = Table([[i] for i in items], colWidths=[CONTENT_W * 0.55])
        tbl.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
        ]))
        return tbl

    left_col  = [[item] for item in left_items]
    right_col = [[item] for item in right_items]

    header_data = [[
        Table(left_col,  colWidths=[CONTENT_W * 0.55]),
        Table(right_col, colWidths=[CONTENT_W * 0.45]),
    ]]
    header_tbl = Table(header_data, colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45])
    header_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    return header_tbl


def _client_block(note, s, t):
    """Bloque de datos del cliente."""
    client = note.client
    elems = [Paragraph(t['client_title'], s['section_title'])]

    if client.client_type == 'individual':
        contacts = list(client.contacts)
        display_name = contacts[0].name if contacts else client.company_name
    else:
        display_name = client.company_name

    elems.append(Paragraph(display_name, s['client_name']))

    if client.tax_id:
        elems.append(Paragraph(f"CIF/NIF: {client.tax_id}", s['client_detail']))
    if client.address:
        elems.append(Paragraph(client.address, s['client_detail']))
    if client.phone:
        elems.append(Paragraph(f"Tel: {client.phone}", s['client_detail']))
    if client.email:
        elems.append(Paragraph(client.email, s['client_detail']))

    box_data = [[Paragraph(t['client_title'], s['section_title'])]]
    inner = []
    for e in elems[1:]:
        inner.append([e])

    outer = Table(
        [[Table(inner, colWidths=[CONTENT_W * 0.55 - 0.4 * cm])]],
        colWidths=[CONTENT_W * 0.55],
    )
    outer.setStyle(TableStyle([
        ('BOX', (0, 0), (-1, -1), 0.5, HexColor('#cccccc')),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f7f8fc')),
    ]))

    title_row = Paragraph(t['client_title'], s['section_title'])
    return Table(
        [[title_row], [outer]],
        colWidths=[CONTENT_W],
    )


def _auto_duration(raw_days, t):
    """Devuelve la duración en la unidad más legible según el número de días."""
    if raw_days < 14:
        return f'{raw_days} {t["days"]}'
    if raw_days < 90:
        weeks = round(raw_days / 7, 1)
        return f'{weeks} {t["weeks"]}'
    months = round(raw_days / 30, 1)
    return f'{months} {t["months"]}'


def _service_table(note, machines, s, t):
    """Tabla de líneas de servicio con columnas: Descripción | F.inicio | F.fin | Duración | Precio unit. | Importe."""
    # 6 columnas: desc(30%) | inicio(12%) | fin(12%) | duración(13%) | precio(16%) | importe(17%)
    col_w = [CONTENT_W * f for f in [0.30, 0.12, 0.12, 0.13, 0.16, 0.17]]
    headers = [t['desc'], t['date_start'], t['date_end'], t['duration'],
               t['unit_price'], t['amount']]
    header_row = [Paragraph(h, s['table_header']) for h in headers]

    fmt = '%d/%m/%Y'
    start_str = note.rental_start.strftime(fmt)
    end_str   = note.rental_end.strftime(fmt) if note.rental_end else '—'

    # Duración automática
    if note.rental_end and note.rental_start:
        raw_days = (note.rental_end - note.rental_start).days or 1
        duration_str = _auto_duration(raw_days, t)
    else:
        duration_str = '—'

    # Precio unitario
    unit_price_str = (f'{note.price_rate:,.2f} €' if note.price_rate
                      else f'({t["fixed"]})')

    # Importe = total_price (base imponible)
    amount_str = (f'{note.total_price:,.2f} €'
                  if note.total_price is not None else '—')

    # Descripción con máquinas
    machine_names = ', '.join(m.name for m in machines) if machines else '—'
    desc_main = f'{t["rental"]} — {machine_names}'
    if note.location:
        desc_main += f'\n{t["location_lbl"]}: {note.location}'

    main_row = [
        Paragraph(desc_main,     s['table_cell']),
        Paragraph(start_str,     s['table_cell']),
        Paragraph(end_str,       s['table_cell']),
        Paragraph(duration_str,  s['table_cell_r']),
        Paragraph(unit_price_str,s['table_cell_r']),
        Paragraph(amount_str,    s['table_cell_r']),
    ]

    rows = [header_row, main_row]

    # Sub-filas por máquina (si hay más de una)
    if len(machines) > 1:
        for m in machines:
            sub_desc = Paragraph(f'{m.code} — {m.name}', s['table_sub'])
            rows.append([sub_desc, '', '', '', '', ''])

    tbl = Table(rows, colWidths=col_w, repeatRows=1)
    tbl.setStyle(TableStyle([
        # Cabecera azul
        ('BACKGROUND',    (0, 0), (-1, 0), NAVY),
        ('TEXTCOLOR',     (0, 0), (-1, 0), WHITE),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0), 8),
        # Filas de datos
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT]),
        # Alineación derecha: Duración, Precio, Importe (cols 3,4,5)
        ('ALIGN',         (3, 0), (-1, -1), 'RIGHT'),
        # Bordes
        ('GRID',          (0, 0), (-1, -1), 0.3, HexColor('#cccccc')),
        ('LINEABOVE',     (0, 0), (-1, 0), 1, NAVY),
        ('LINEBELOW',     (0, 0), (-1, 0), 1, NAVY),
        # Padding
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
    ]))
    return tbl


def _totals_block(note, s, t):
    """Desglose fiscal alineado a la derecha."""
    base   = note.total_price or 0.0
    vat    = round(base * 0.21, 2)
    total  = round(base + vat, 2)

    sep = HRFlowable(width=CONTENT_W * 0.35, thickness=0.5,
                     color=HexColor('#cccccc'), spaceAfter=2, spaceBefore=2)

    col_label = CONTENT_W * 0.65
    col_value = CONTENT_W * 0.35

    rows = [
        [Paragraph(t['tax_base'], s['total_label']),
         Paragraph(f'{base:,.2f} €', s['total_value'])],
        [Paragraph(t['vat'], s['total_label']),
         Paragraph(f'{vat:,.2f} €', s['total_value'])],
        ['', ''],   # fila separadora
        [Paragraph(t['total'], s['total_label_bold']),
         Paragraph(f'{total:,.2f} €', s['total_value_bold'])],
    ]

    tbl = Table(rows, colWidths=[col_label, col_value])
    tbl.setStyle(TableStyle([
        ('ALIGN',        (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN',       (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING',  (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING',   (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING',(0, 0), (-1, -1), 3),
        # Línea separadora antes del TOTAL
        ('LINEABOVE',    (0, 3), (-1, 3), 0.7, NAVY),
        # Fondo para el total
        ('BACKGROUND',   (0, 3), (-1, 3), LIGHT),
        # Fila vacía separadora — sin padding
        ('TOPPADDING',   (0, 2), (-1, 2), 0),
        ('BOTTOMPADDING',(0, 2), (-1, 2), 0),
    ]))
    return tbl


def _footer_block(s, t):
    return Table(
        [
            [Paragraph(t['footer'], s['footer'])],
            [Paragraph(t['bank'],   s['bank'])],
        ],
        colWidths=[CONTENT_W],
    )


# ── Función principal ─────────────────────────────────────────────────────────

def generate_invoice_pdf(note, machines, lang='es') -> bytes:
    buf = BytesIO()

    # Canvas personalizado con idioma
    class _Canvas(pdf_canvas.Canvas):
        def __init__(self, *args, **kwargs):
            pdf_canvas.Canvas.__init__(self, *args, **kwargs)
            self._saved_page_states = []

        def showPage(self):
            self._saved_page_states.append(dict(self.__dict__))
            self._startPage()

        def save(self):
            total = len(self._saved_page_states)
            tr = STRINGS.get(lang, STRINGS['es'])
            for state in self._saved_page_states:
                self.__dict__.update(state)
                if total > 1:
                    self.setFont('Helvetica', 7.5)
                    self.setFillColor(GREY)
                    self.drawRightString(
                        PAGE_W - MARGIN, 1.2 * cm,
                        f"{tr['page']} {self._pageNumber} {tr['of']} {total}",
                    )
                pdf_canvas.Canvas.showPage(self)
            pdf_canvas.Canvas.save(self)

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=2.5 * cm,
        title=f"{STRINGS.get(lang, STRINGS['es'])['invoice']} {note.invoice_number}",
        author=COMPANY['name'],
    )

    t = STRINGS.get(lang, STRINGS['es'])
    s = _styles()

    story = [
        _header(note, s, t),
        HRFlowable(width=CONTENT_W, thickness=1, color=NAVY,
                   spaceAfter=0.4 * cm, spaceBefore=0.3 * cm),
        _client_block(note, s, t),
        Spacer(1, 0.5 * cm),
        _service_table(note, machines, s, t),
        Spacer(1, 0.4 * cm),
        _totals_block(note, s, t),
        Spacer(1, 1.2 * cm),
        HRFlowable(width=CONTENT_W, thickness=0.5, color=HexColor('#cccccc'),
                   spaceAfter=0.3 * cm),
        _footer_block(s, t),
    ]

    doc.build(story, canvasmaker=_Canvas)
    return buf.getvalue()
