from pypdf import PdfReader, PdfWriter
import io

def rotate_pdf(file, angle):
    reader = PdfReader(file)
    writer = PdfWriter()

    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)

    output = io.BytesIO()
    writer.write(output)
    output.seek(0)
    return output
