"""Fake curriculum-design pages in the same table layout as the real documents. No real content."""
from collections import namedtuple

Page = namedtuple("Page", "pdf_page printed_page text")
DOT = "\u2022"


def row(c0="", c1="", c2="", c3="", c4="", widths=(14, 22, 36, 46)):
    return (c0.ljust(widths[0]) + c1.ljust(widths[1]) + c2.ljust(widths[2]) + c3.ljust(widths[3]) + c4).rstrip()


def rubric_row(a="", b="", c="", d="", e=""):
    return (a.ljust(20) + b.ljust(25) + c.ljust(25) + d.ljust(25) + e).rstrip()


def header(widths=(14, 22, 36, 46)):
    return [
        row("Strand", "Sub-Strand", "Specific Learning", "Suggested Learning Experiences", "Suggested Key", widths),
        row("", "", "Outcomes", "", "Inquiry", widths),
        row("", "", "", "", "Question(s)", widths),
    ]


PAGE_1 = "\n".join([
    "TABLE OF CONTENTS",
    "STRAND 1.0: DEMO STRAND ........................ 13",
    "",
    "STRAND 1.0: DEMO STRAND",
    *header(),
    row("1.0", "1.1 Demo", "By the end of the sub-strand,", "The learner is guided to:", "1. What is a demo?"),
    row("Demo", "Numbers", "the learner should be able to:", "", "2. Why demo?"),
    row("", "(20 Lessons)", "a)  demo outcome one,", f"{DOT}  demo experience one", ""),
    row("", f"{DOT}  Demo topic", "b)  demo outcome two that", "continues here", ""),
    row("", "", "     wraps to the next line,", f"{DOT}  demo experience two with a hyphen-", ""),
    row("", "", "c)  appreciate demo", "   ated word", ""),
    "Core competencies to be developed:",
    "Critical thinking and problem solving: learner does a demo.",
    "Values:",
    "Unity: learner works together.",
    "Pertinent and Contemporary Issues (PCIs):",
    "Learner does something safely.",
    "Link to other learning areas:",
    "Learner links demo to Creative Arts.",
    "",
    "13",
])

W2 = (17, 20, 40, 44)  # a second table whose columns sit in different places
PAGE_2 = "\n".join([
    *header(W2),
    row("1.0", "1.2 Second", "a)  second outcome", f"{DOT}  second experience", "How do we do the second?", W2),
    row("", "( 6 Lesso ns )", "b)  another outcome", f"{DOT}  another experience", "", W2),
    "Core competencies to be developed:",
    "Self -effi cacy: learner is confident.",
    "Values:",
    "Love: learner cares.",
    "Pertinent and Contemporary Issues (PCIs):",
    "Safety: learner stays safe.",
    "Link to other learning areas:",
    "Learner links this to Science.",
    "Suggested Assessment Rubric",
    rubric_row("Indicator", "Exceeds Expectations", "Meets Expectations", "Approaches Expectations", "Below Expectations"),
    rubric_row("Ability to demo", "Demo exceeds", "Demo meets", "Demo approaches", "Demo below"),
    rubric_row("one thing", "wraps", "", "", "here"),
    rubric_row("Ability to demo two", "Two exceeds", "Two meets", "Two approaches", "Two below"),
    "",
    "14",
])

PAGE_3 = "\n".join([
    "STRAND 2.0: SECOND DEMO STRAND",
    *header(),
    row("2.0", "2.1 Third", "a)  third outcome", f"{DOT}  third experience", "A third question?"),
    row("", "(5 Lessons)", "", "", ""),
    "Core competencies to be developed:",
    "Citizenship: learner votes.",
    "APPENDICES",
    "Everything after this line is ignored.",
    "15",
])

PAGES = [Page(13, "13", PAGE_1), Page(14, "14", PAGE_2), Page(15, "15", PAGE_3)]
