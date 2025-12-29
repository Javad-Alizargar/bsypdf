import io
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from PIL import Image

def apply_overlay_fullpage(pdf_file, overlay_png_path, page_number, page_w_pt, page_h_pt):
    """
    Applies a transparent overlay PNG (same aspect as the page preview) onto a selected PDF page.
    The overlay is drawn full-page (0,0 -> page_w,page_h), so it lands exactly where the user drew.
    """
    reader = PdfReader(pdf_file)
    writer = PdfWriter()

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=(float(page_w_pt), float(page_h_pt)))

    # Draw the overlay to cover the full page
    can.drawImage(
        overlay_png_path,
        0,
        0,
        width=float(page_w_pt),
        height=float(page_h_pt),
        mask='auto'
    )
    can.save()
    packet.seek(0)

    overlay_reader = PdfReader(packet)
    overlay_page = overlay_reader.pages[0]

    for i, page in enumerate(reader.pages):
        if i == page_number:
            page.merge_page(overlay_page)
        writer.add_page(page)

    out = io.BytesIO()
    writer.write(out)
    out.seek(0)
    return out

def extract_ink_overlay(canvas_rgba, background_rgb, diff_threshold=10):
    """
    Given:
      - canvas_rgba: HxWx4 uint8 (result from st_canvas)
      - background_rgb: HxWx3 uint8 (rendered PDF page preview)

    Returns a PIL RGBA image where ONLY ink strokes remain (transparent elsewhere).
    This prevents a white/opaque rectangle covering the PDF text.
    """
    import numpy as np

    c = canvas_rgba[..., :3].astype(np.int16)
    b = background_rgb.astype(np.int16)

    # pixels that differ from background are considered ink
    diff = np.abs(c - b).sum(axis=2)
    ink_mask = diff > diff_threshold

    # Start with fully transparent
    out = np.zeros_like(canvas_rgba, dtype=np.uint8)

    # Copy ink RGB from canvas
    out[..., :3] = canvas_rgba[..., :3]

    # Alpha: 255 where ink exists, else 0
    out[..., 3] = (ink_mask * 255).astype(np.uint8)

    return Image.fromarray(out, mode="RGBA")
