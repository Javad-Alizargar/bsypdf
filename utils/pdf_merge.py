from pypdf import PdfReader, PdfWriter
import io

def merge_pdfs(files):
    writer = PdfWriter()

    for f in files:
        reader = PdfReader(f)
        for page in reader.pages:
            writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output
