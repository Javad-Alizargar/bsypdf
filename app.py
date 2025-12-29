import streamlit as st
from utils.pdf_merge import merge_pdfs
from utils.split import split_pdf
from utils.rotate import rotate_pdf

st.set_page_config(page_title="Quick PDF Tools", layout="centered")

st.title("Quick PDF Tools")
st.write("Free PDF merge, split, rotate, and sign. No signup required.")

tool = st.selectbox(
    "Choose a tool",
    ["Merge PDF", "Split PDF", "Rotate PDF", "Edit / Sign PDF"]
)

# ---------------- Merge PDF ----------------
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

# ---------------- Split PDF ----------------
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

# ---------------- Rotate PDF ----------------
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

# ---------------- Edit / Sign PDF ----------------
elif tool == "Edit / Sign PDF":
    import tempfile
    import numpy as np
    import fitz  # PyMuPDF
    from PIL import Image
    from pypdf import PdfReader
    from streamlit_drawable_canvas import st_canvas
    from utils.edit import apply_overlay_fullpage, extract_ink_overlay

    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file:
        # Read PDF metadata
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
            stroke_width = st.slider("Pen size", 1, 12, 3)
        with col2:
            stroke_color = st.color_picker("Pen color", "#000000")

        # Render selected page as image
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(page_num - 1)

        zoom = 2.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # Resize for UI
        max_w = 900
        if page_img.width > max_w:
            new_h = int(page_img.height * (max_w / page_img.width))
            page_img_disp = page_img.resize((max_w, new_h))
        else:
            page_img_disp = page_img

        st.caption("Draw directly on the page preview. Only your ink will be applied (no white box).")

        # Save background image to temp file (REQUIRED for Streamlit Cloud)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as bg_tmp:
            page_img_disp.save(bg_tmp.name)
            bg_image_path = bg_tmp.name

        canvas_result = st_canvas(
            background_image=bg_image_path,
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
                # Extract ink only
                bg_np = np.array(page_img_disp, dtype=np.uint8)
                canvas_np = canvas_result.image_data.astype(np.uint8)

                ink_img = extract_ink_overlay(
                    canvas_np,
                    bg_np,
                    diff_threshold=12
                )

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    ink_img.save(tmp.name)

                    p = pdf_reader.pages[page_num - 1]
                    page_w_pt = float(p.mediabox.width)
                    page_h_pt = float(p.mediabox.height)

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
