from pathlib import Path

import pypdfium2

from assistant import config


def list_pdfs() -> list[Path]:
    return sorted(config.DOCUMENTS_DIR.glob("*/*.pdf"))


def relative_path(pdf: Path) -> str:
    return pdf.relative_to(config.DOCUMENTS_DIR).as_posix()


def page_count(pdf: Path) -> int:
    document = pypdfium2.PdfDocument(pdf)
    count = len(document)
    document.close()
    return count


def title(pdf: Path) -> str:
    # Hasil scan biasanya tidak punya judul di metadata, jadi nama file dipakai sebagai gantinya
    document = pypdfium2.PdfDocument(pdf)
    metadata_title = document.get_metadata_dict().get("Title")
    document.close()
    return metadata_title or pdf.stem


def page_file(pdf: Path, page_number: int) -> Path:
    # Contoh: data/pages/HR/SOP-HR-002 Cuti dan Izin rev04/005.md
    return config.PAGES_DIR / relative_path(pdf).removesuffix(".pdf") / f"{page_number:03d}.md"


def list_documents() -> list[tuple[str, str]]:
    return [(pdf.parent.name, title(pdf)) for pdf in list_pdfs()]
