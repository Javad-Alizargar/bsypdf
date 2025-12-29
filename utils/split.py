from pypdf import PdfReader, PdfWriter
import io

def split_pdf(file, page_range):
    reader = PdfReader(file)
    writer = PdfWriter()

    # Parse "start-end"
    try:
        start_str, end_str = page_range.split("-")
        start, end = int(start_str.strip()), int(end_str.strip())
    except Exception:
        raise ValueError("Invalid page range. Use format like 1-3")

    if start < 1 or end < start:
        raise ValueError("Invalid page range. Ensure start >= 1 and end >= start")

    n_pages = len(reader.pages)
    if end > n_pages:
        raise ValueError(f"PDF has {n_pages} pages. Your end page is {end}.")

    for i in range(start - 1, end):
        writer.add_page(reader.pages[i])

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output
