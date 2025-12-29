import streamlit as st
from utils.pdf_merge import merge_pdfs
from utils.split import split_pdf
from utils.rotate import rotate_pdf
from utils.pdf_merge import merge_pdfs

st.set_page_config(page_title="Quick PDF Tools", layout="centered")

st.title("Quick PDF Tools")
st.write("Free PDF merge, split, and rotate. No signup required.")

tool = st.selectbox(
    "Choose a tool",
    ["Merge PDF", "Split PDF", "Rotate PDF", "Edit / Sign PDF"]
)

if tool == "Merge PDF":
    uploaded_files = st.file_uploader(
        "Upload PDF files",
        type="pdf",
        accept_multiple_files=True
    )
    if uploaded_files and st.button("Merge"):
        output = merge_pdfs(uploaded_files)
        st.download_button(
            "Download merged PDF",
            output,
            file_name="merged.pdf",
            mime="application/pdf"
        )

elif tool == "Split PDF":
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    page_range = st.text_input("Page range (e.g. 1-3)")
    if uploaded_file and page_range and st.button("Split"):
        output = split_pdf(uploaded_file, page_range)
        st.download_button(
            "Download split PDF",
            output,
            file_name="split.pdf",
            mime="application/pdf"
        )

elif tool == "Rotate PDF":
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    angle = st.selectbox("Rotation angle", [90, 180, 270])
    if uploaded_file and st.button("Rotate"):
        output = rotate_pdf(uploaded_file, angle)
        st.download_button(
            "Download rotated PDF",
            output,
            file_name="rotated.pdf",
            mime="application/pdf"
        )

# -------- Edit / Sign PDF --------
if tool == "Edit / Sign PDF":
    import io
    import tempfile
    import numpy as np
    import fitz  # pymupdf
    from PIL import Image
    from pypdf import PdfReader
    from streamlit_drawable_canvas import st_canvas
    from utils.edit import apply_overlay_fullpage, extract_ink_overlay

    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file:
        # Read PDF with pypdf for metadata (page count + page size in points)
        pdf_reader = PdfReader(uploaded_file)
        total_pages = len(pdf_reader.pages)

        page_num = st.number_input(
            "Select page number",
            min_value=1,
            max_value=total_pages,
            value=1
        )

        # Pen controls
        col1, col2 = st.columns(2)
        with col1:
            stroke_width = st.slider("Pen size", min_value=1, max_value=12, value=3)
        with col2:
            stroke_color = st.color_picker("Pen color", value="#000000")

        # Render selected page to an image preview using PyMuPDF
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(page_num - 1)

        # Render at a moderate zoom for clarity; we will display resized if needed
        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Resize preview to a reasonable width for UI, keeping aspect ratio
        max_w = 900
        if page_img.width > max_w:
            new_h = int(page_img.height * (max_w / page_img.width))
            page_img_disp = page_img.resize((max_w, new_h))
        else:
            page_img_disp = page_img

        st.caption("Draw directly on the page preview below. Only your ink will be applied (no white box).")

        canvas_result = st_canvas(
            background_image=page_img_disp,
            height=page_img_disp.height,
            width=page_img_disp.width,
            drawing_mode="freedraw",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            key="sign_canvas_v4",
        )

        if st.button("Apply Signature"):
            if canvas_result.image_data is None:
                st.error("No drawing detected.")
            else:
                # Convert background to numpy for ink extraction
                bg_np = np.array(page_img_disp, dtype=np.uint8)
                canvas_np = canvas_result.image_data.astype(np.uint8)

                # Extract only ink strokes as transparent RGBA
                ink_img = extract_ink_overlay(canvas_np, bg_np, diff_threshold=12)

                # Save overlay PNG
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    ink_img.save(tmp.name)

                    # Get true PDF page size in points (for correct full-page overlay)
                    p = pdf_reader.pages[page_num - 1]
                    page_w_pt = float(p.mediabox.width)
                    page_h_pt = float(p.mediabox.height)

                    # Apply as full-page overlay (scaled to PDF page)
                    uploaded_file.seek(0)
                    output_pdf = apply_overlay_fullpage(
                        uploaded_file,
                        tmp.name,
                        page_num - 1,
                        page_w_pt,
                        page_h_pt
                    )

                st.download_button(
                    "Download signed PDF",
                    output_pdf,
                    file_name="signed.pdf",
                    mime="application/pdf"
                )
