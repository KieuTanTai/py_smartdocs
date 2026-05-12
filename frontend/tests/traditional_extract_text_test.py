from pypdf import PdfReader
from pathlib import Path


def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

if __name__ == "__main__":
    root_dir = Path(__file__).resolve().parents[2]
    pdf_path = root_dir / "docs" / "pdfs_test" / "Báo cáo tài chính Kiểm toán năm 2025.pdf"
    extracted_text = extract_text_from_pdf(pdf_path)
    file_name = Path(pdf_path).stem
    print("is empty:", not extracted_text.strip())
    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / f"output_{file_name}.md", "w") as f:
        f.write(extracted_text)
