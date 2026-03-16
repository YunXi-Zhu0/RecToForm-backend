from src.core.config import TESTS_DIR
from easyofd import OFD

def ofd_to_pdf(path):
    ofd = OFD()
    ofd.read(path, fmt="path")
    pdf_bytes = ofd.to_pdf()
    with open(TESTS_DIR / "test.pdf", "wb") as f:
        f.write(pdf_bytes)

    ofd.disposal()

if __name__ == "__main__":
    path = TESTS_DIR / "130.ofd"
    ofd_to_pdf(path)
