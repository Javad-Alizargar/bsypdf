from pypdf import PdfMerger
import io

def merge_pdfs(files):
    merger = PdfMerger()
    for f in files:
        merger.append(f)
    output = io.BytesIO()
    merger.write(output)
    merger.close()
    output.seek(0)
    return output
