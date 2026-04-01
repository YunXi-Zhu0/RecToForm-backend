from easyofd import OFD

from src.core.config import TESTS_DIR


def ofd_to_pdf(path):
    ofd = OFD()
    ofd.read(path, fmt="path")
    pdf_bytes = ofd.to_pdf()
    output_dir = TESTS_DIR / "scripts" / "outputs" / "ofd"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "test.pdf", "wb") as f:
        f.write(pdf_bytes)

    ofd.disposal()


if __name__ == "__main__":
    path = TESTS_DIR / "fixtures" / "invoices" / "130.ofd"
    ofd_to_pdf(path)
