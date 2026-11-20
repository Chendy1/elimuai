"""Pure PDF text extraction (no database). Keeps the PDF page number and, where it can be detected,
the number printed on the page, because the two differ (front matter, restarted numbering)."""
import io
import re
from dataclasses import dataclass

from pypdf import PdfReader
from pypdf.errors import PyPdfError

# Some source PDFs encode Roman numerals with odd glyphs (for example "iii" comes out as a
# different character). These are the ones seen so far; add more if a new source needs it.
GLYPH_FIXES = str.maketrans({"\u015d": "i", "\u01c0": "v", "\u01c6": "x"})
PAGE_TOKEN = re.compile(r"^(?:[ivxlcdm]{1,6}|\d{1,3})$", re.IGNORECASE)


@dataclass(frozen=True)
class ExtractedPage:
    pdf_page: int  # 1-based position in the file
    printed_page: str | None  # the number printed on the page, if one was found
    text: str


def clean_text(raw: str) -> str:
    """Remove characters PostgreSQL rejects or that are only noise; keep the layout."""
    raw = raw.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n")
    lines = ["".join(ch for ch in line if ch == "\t" or ch >= " ").rstrip() for line in raw.split("\n")]
    text = "\n".join(lines).strip("\n")
    return re.sub(r"\n{3,}", "\n\n", text)


def _candidate_lines(raw: str) -> list[str]:
    lines = []
    for line in raw.splitlines():
        stripped = "".join(ch for ch in line if ch >= " ").strip()
        if stripped:
            lines.append(stripped)
    return lines


def detect_printed_page(raw: str) -> str | None:
    """Look for a lone page number on the last two or first two non-empty lines."""
    lines = _candidate_lines(raw)
    if not lines:
        return None
    ordered = [lines[-1], lines[-2] if len(lines) > 1 else "", lines[0], lines[1] if len(lines) > 1 else ""]
    for candidate in ordered:
        token = candidate.translate(GLYPH_FIXES).strip()
        if token and PAGE_TOKEN.match(token):
            return token.lower()
    return None


def extract_pdf_pages(data: bytes) -> list[ExtractedPage]:
    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ValueError("Encrypted PDFs are not supported.")
        pages = []
        for number, page in enumerate(reader.pages, start=1):
            try:
                raw = page.extract_text(extraction_mode="layout")
            except Exception:  # fall back to the simpler extractor
                raw = page.extract_text()
            pages.append(ExtractedPage(number, detect_printed_page(raw), clean_text(raw)))
    except PyPdfError as exc:
        raise ValueError("That file is not a readable PDF.") from exc
    return pages
