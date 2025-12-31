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

# ---------------- Edit / Sign PDF (OPTION A) ----------------
elif tool == "Edit / Sign PDF":
    import numpy as np
    import fitz  # PyMuPDF
    import tempfile
    from PIL import Image
    from pypdf import PdfReader
    from streamlit_drawable_canvas import st_canvas
    from utils.edit import apply_overlay_fullpage

    uploaded_file = st.file_uploader("Upload PDF", type="pdf")

    if uploaded_file:
        # ---- Persist page number ----
        if "page_num" not in st.session_state:
            st.session_state.page_num = 1

        pdf_reader = PdfReader(uploaded_file)
        total_pages = len(pdf_reader.pages)

        st.session_state.page_num = st.number_input(
            "Select page number",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.page_num,
            step=1
        )

        # ---- Pen controls ----
        col1, col2 = st.columns(2)
        with col1:
            stroke_width = st.slider("Pen size", 1, 12, 3)
        with col2:
            stroke_color = st.color_picker("Pen color", "#000000")

        # ---- Render selected page (preview only) ----
        uploaded_file.seek(0)
        pdf_bytes = uploaded_file.read()
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page = doc.load_page(st.session_state.page_num - 1)

        zoom = 2.0
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
        page_img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        st.subheader(f"Page {st.session_state.page_num} preview (read-only)")
        st.image(page_img, use_column_width=True)

        st.subheader("Sign here (applied to selected page)")

        # ---- Signing canvas (same aspect, separate area) ----
        canvas_result = st_canvas(
            height=page_img.height,
            width=page_img.width,
            drawing_mode="freedraw",
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color="rgba(0,0,0,0)",
            key=f"canvas_page_{st.session_state.page_num}",
        )

        if st.button("Apply Signature"):
            if canvas_result.image_data is None:
                st.error("No drawing detected.")
            else:
                # EVERYTHING drawn is ink
                canvas_np = canvas_result.image_data.astype(np.uint8)
                ink_img = Image.fromarray(canvas_np, mode="RGBA")

                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    ink_img.save(tmp.name)

                    p = pdf_reader.pages[st.session_state.page_num - 1]
                    page_w_pt = float(p.mediabox.width)
                    page_h_pt = float(p.mediabox.height)

                    uploaded_file.seek(0)
                    output_pdf = apply_overlay_fullpage(
                        uploaded_file,
                        tmp.name,
                        st.session_state.page_num - 1,
                        page_w_pt,
                        page_h_pt
                    )

                st.success("Signature applied to PDF.")
                st.download_button(
                    "Download signed PDF",
                    output_pdf,
                    file_name="signed.pdf",
                    mime="application/pdf"
                )
