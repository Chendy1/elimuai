import pytest

from app.importer.pdf_text import clean_text, detect_printed_page, extract_pdf_pages
from tests.pdf_factory import make_pdf


def test_extracts_every_page_in_order_with_text():
    pdf = make_pdf([["Demo cover"], ["Demo foreword", "ii"], ["Demo strand", "second line", "13"]])
    pages = extract_pdf_pages(pdf)
    assert [p.pdf_page for p in pages] == [1, 2, 3]
    assert "Demo foreword" in pages[1].text
    assert "second line" in pages[2].text


def test_printed_page_is_detected_separately_from_the_pdf_page():
    pdf = make_pdf([["Demo cover"], ["Demo front matter", "ii"], ["Demo body", "13"], ["Demo body", "text only"]])
    printed = [p.printed_page for p in extract_pdf_pages(pdf)]
    assert printed == [None, "ii", "13", None]


def test_garbled_roman_numerals_are_recognised():
    assert detect_printed_page("Foreword\nsome text\n\u015d\u015d\u015d\x03") == "iii"
    assert detect_printed_page("Preface\nsome text\n\u015d\u01c0\x03") == "iv"
    assert detect_printed_page("Acknowledgement\ntext\n\u01c0\x03") == "v"


def test_no_page_number_means_none():
    assert detect_printed_page("") is None
    assert detect_printed_page("A heading\nA sentence that is not a number") is None


def test_clean_text_removes_characters_postgres_rejects():
    assert clean_text("a\x00b\x03c\r\n\r\n\r\n\r\nd   ") == "abc\n\nd"


def test_unreadable_files_are_rejected_with_a_clear_error():
    with pytest.raises(ValueError):
        extract_pdf_pages(b"this is not a pdf")
