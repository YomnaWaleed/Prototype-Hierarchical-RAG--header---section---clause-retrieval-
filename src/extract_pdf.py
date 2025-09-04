from pypdf import PdfReader
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    pages = []

    for p in reader.pages:
        text = p.extract_text() or ""
        pages.append(text)
    return "\n\n".join(pages)


def save_text(pdf_path: str, out_txt_path: str):
    text = extract_text_from_pdf(pdf_path=pdf_path)
    Path(out_txt_path).write_text(text, encoding="utf-8")


# PDF paths
pdf1 = "../data/raw/Automotive_SPICE_PAM_31_EN.pdf"
out1 = "../data/txt/automotivespice.txt"

pdf2 = "../data/raw/AUTOSAR_SWS_ECUStateManager.pdf"
out2 = "../data/txt/autosar_ecum.txt"

# Run extraction
save_text(pdf1, out1)
save_text(pdf2, out2)
