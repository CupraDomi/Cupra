import base64
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                Table, TableStyle, HRFlowable, Image as RLImage)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from config import Config

BRAND_BLUE  = colors.HexColor('#1e3a5f')
BRAND_LIGHT = colors.HexColor('#e8f0f7')
GREY        = colors.HexColor('#555555')
LIGHT_GREY  = colors.HexColor('#f5f5f5')


def generate_albaran_pdf(note, machines) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle('normal', fontSize=9, leading=13, textColor=GREY)
    style_bold   = ParagraphStyle('bold', fontSize=9, leading=13, fontName='Helvetica-Bold')
    style_title  = ParagraphStyle('title', fontSize=16, leading=20,
                                  fontName='Helvetica-Bold', textColor=BRAND_BLUE)
    style_small  = ParagraphStyle('small', fontSize=8, leading=11, textColor=GREY)
    style_center = ParagraphStyle('center', fontSize=9, alignment=TA_CENTER)
    style_right  = ParagraphStyle('right', fontSize=9, alignment=TA_RIGHT)

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f'<b>{Config.COMPANY_NAME}</b>', style_title),
        Paragraph(
            f'{Config.COMPANY_ADDRESS}<br/>'
            f'Tel: {Config.COMPANY_PHONE}<br/>'
            f'{Config.COMPANY_EMAIL}<br/>'
            f'CIF: {Config.COMPANY_CIF}',
            style_small
        ),
    ]]
    header_table = Table(header_data, colWidths=[100*mm, 70*mm])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    story.append(header_table)
    story.append(HRFlowable(width='100%', thickness=2, color=BRAND_BLUE, spaceAfter=4*mm))

    # ── Albarán title ─────────────────────────────────────────────────────────
    title_data = [[
        Paragraph(f'ALBARÁN DE ALQUILER', ParagraphStyle(
            'atitle', fontSize=13, fontName='Helvetica-Bold',
            textColor=colors.white, alignment=TA_CENTER)),
        Paragraph(f'{note.albaran_number}', ParagraphStyle(
            'anum', fontSize=13, fontName='Helvetica-Bold',
            textColor=colors.white, alignment=TA_CENTER)),
    ]]
    title_table = Table(title_data, colWidths=[100*mm, 70*mm])
    title_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BRAND_BLUE),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 4*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4*mm),
    ]))
    story.append(title_table)
    story.append(Spacer(1, 5*mm))

    # ── Client + dates block ──────────────────────────────────────────────────
    client = note.client
    status_map = {'active': 'Activo', 'closed': 'Cerrado', 'cancelled': 'Cancelado'}
    info_data = [
        ['CLIENTE', '', 'ALBARÁN', ''],
        [
            Paragraph(f'<b>{client.company_name}</b>', style_bold),
            '',
            Paragraph(f'Nº: <b>{note.albaran_number}</b>', style_bold),
            '',
        ],
        [
            Paragraph(f'Código: {client.client_code}', style_normal),
            '',
            Paragraph(f'Estado: {status_map.get(note.status, note.status)}', style_normal),
            '',
        ],
        [
            Paragraph(f'CIF/DNI: {client.tax_id or "—"}', style_normal),
            '',
            Paragraph(f'Creado por: {note.created_by}', style_normal),
            '',
        ],
        [
            Paragraph(f'Tel: {client.phone or "—"}', style_normal),
            '',
            Paragraph(f'Fecha creación: {note.created_at.strftime("%d/%m/%Y")}', style_normal),
            '',
        ],
    ]
    info_table = Table(info_data, colWidths=[80*mm, 10*mm, 70*mm, 10*mm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (1,0), BRAND_LIGHT),
        ('BACKGROUND', (2,0), (3,0), BRAND_LIGHT),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 8),
        ('TEXTCOLOR', (0,0), (-1,0), BRAND_BLUE),
        ('TOPPADDING', (0,0), (-1,-1), 2*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
        ('LINEBELOW', (0,0), (-1,0), 0.5, BRAND_BLUE),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('SPAN', (0,1), (1,1)), ('SPAN', (2,1), (3,1)),
        ('SPAN', (0,2), (1,2)), ('SPAN', (2,2), (3,2)),
        ('SPAN', (0,3), (1,3)), ('SPAN', (2,3), (3,3)),
        ('SPAN', (0,4), (1,4)), ('SPAN', (2,4), (3,4)),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 5*mm))

    # ── Rental details ────────────────────────────────────────────────────────
    start_str = note.rental_start.strftime('%d/%m/%Y')
    end_str   = note.rental_end.strftime('%d/%m/%Y') if note.rental_end else 'Abierto'
    rental_data = [
        ['DETALLES DEL ALQUILER', '', ''],
        ['Obra / Ubicación', 'Fecha inicio', 'Fecha fin'],
        [note.location or '—', start_str, end_str],
    ]
    rental_table = Table(rental_data, colWidths=[80*mm, 45*mm, 45*mm])
    rental_table.setStyle(TableStyle([
        ('SPAN', (0,0), (2,0)),
        ('BACKGROUND', (0,0), (2,0), BRAND_LIGHT),
        ('FONTNAME', (0,0), (2,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (2,0), 8),
        ('TEXTCOLOR', (0,0), (2,0), BRAND_BLUE),
        ('BACKGROUND', (0,1), (2,1), LIGHT_GREY),
        ('FONTNAME', (0,1), (2,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (2,1), 8),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('TOPPADDING', (0,0), (-1,-1), 2*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
        ('GRID', (0,1), (-1,-1), 0.3, colors.lightgrey),
    ]))
    story.append(rental_table)
    story.append(Spacer(1, 4*mm))

    # ── Machines table ────────────────────────────────────────────────────────
    machine_rows = [['Código', 'Descripción', 'Categoría', 'Especificaciones']]
    for m in machines:
        machine_rows.append([
            m.code, m.name,
            m.category,
            (m.specs or '—')[:60],
        ])
    machine_table = Table(machine_rows, colWidths=[30*mm, 60*mm, 30*mm, 50*mm])
    machine_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), BRAND_BLUE),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('GRID', (0,0), (-1,-1), 0.3, colors.lightgrey),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT_GREY]),
        ('TOPPADDING', (0,0), (-1,-1), 2*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(machine_table)
    story.append(Spacer(1, 4*mm))

    # ── Pricing ───────────────────────────────────────────────────────────────
    mode_label = 'Precio cerrado (fijo)' if note.pricing_mode == 'closed' else 'Precio abierto (por tarifa)'
    if note.pricing_mode == 'closed':
        price_detail = f'{note.total_price:,.2f} €' if note.total_price else '—'
    else:
        unit_map = {'day': 'día', 'week': 'semana', 'month': 'mes'}
        if note.price_rate:
            price_detail = f'{note.price_rate:,.2f} € / {unit_map.get(note.price_unit, note.price_unit or "")}'
        else:
            price_detail = '—'
        if note.total_price:
            price_detail += f'   →   Total: {note.total_price:,.2f} €'

    pricing_data = [
        ['PRECIO', ''],
        ['Modalidad', mode_label],
        ['Importe', price_detail],
    ]
    pricing_table = Table(pricing_data, colWidths=[40*mm, 130*mm])
    pricing_table.setStyle(TableStyle([
        ('SPAN', (0,0), (1,0)),
        ('BACKGROUND', (0,0), (1,0), BRAND_LIGHT),
        ('FONTNAME', (0,0), (1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (1,0), BRAND_BLUE),
        ('FONTNAME', (0,1), (0,-1), 'Helvetica-Bold'),
        ('GRID', (0,1), (-1,-1), 0.3, colors.lightgrey),
        ('TOPPADDING', (0,0), (-1,-1), 2*mm),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2*mm),
    ]))
    story.append(pricing_table)
    story.append(Spacer(1, 4*mm))

    # ── Notes ─────────────────────────────────────────────────────────────────
    if note.notes:
        story.append(Paragraph('<b>Observaciones:</b>', style_bold))
        story.append(Paragraph(note.notes, style_normal))
        story.append(Spacer(1, 4*mm))

    # ── Signatures ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10*mm))

    style_sig_info = ParagraphStyle(
        'sig_info', fontSize=7, leading=10, textColor=GREY, alignment=TA_CENTER
    )

    client_col_content = None
    if note.signature_data and note.signed_at:
        try:
            raw = note.signature_data
            b64 = raw.split(',', 1)[1] if ',' in raw else raw
            sig_img = RLImage(io.BytesIO(base64.b64decode(b64)), width=65*mm, height=22*mm)
            sig_img.hAlign = 'CENTER'
            inner = Table(
                [[sig_img],
                 [Paragraph(f'<b>{note.signer_name}</b>',
                            ParagraphStyle('sn', fontSize=8, fontName='Helvetica-Bold',
                                           alignment=TA_CENTER, leading=12))],
                 [Paragraph(
                     f'Firmado digitalmente el {note.signed_at.strftime("%d/%m/%Y a las %H:%M")}',
                     style_sig_info)]],
                colWidths=[83*mm],
            )
            inner.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'),
                                       ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            client_col_content = inner
        except Exception:
            client_col_content = None

    if client_col_content is None:
        client_col_content = Paragraph(
            'Firma cliente\n\n\n\n____________________________', style_center
        )

    sig_data = [[
        client_col_content,
        Paragraph('Firma empresa\n\n\n\n____________________________', style_center),
    ]]
    sig_table = Table(sig_data, colWidths=[85*mm, 85*mm])
    sig_table.setStyle(TableStyle([
        ('ALIGN',      (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4*mm),
    ]))
    story.append(sig_table)

    doc.build(story)
    return buf.getvalue()
