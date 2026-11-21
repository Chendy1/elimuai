"""Parser for curriculum designs laid out as one table per sub-strand (the Grade 6 Mathematics
layout): Strand | Sub-strand and topics | Learning outcomes | Learning experiences | Inquiry questions,
followed by competency / value / PCI / link paragraphs, and a rubric per strand.

It works on the layout text stored by the importer, finds each table's column positions from its
own header, and records a warning for anything that does not look right. Its output is only ever a
PROPOSAL: a person reviews every record against the source page before it can be published."""
import re
from dataclasses import dataclass, field
from typing import Protocol

COMPETENCY_CODES = {
    "communication and collaboration": "communication_collaboration",
    "critical thinking and problem solving": "critical_thinking",
    "creativity and imagination": "creativity_imagination",
    "citizenship": "citizenship",
    "digital literacy": "digital_literacy",
    "learning to learn": "learning_to_learn",
    "self-efficacy": "self_efficacy",
    "self efficacy": "self_efficacy",
}
def _spaced(name: str) -> str:
    """Regex for a name that tolerates stray spaces between any letters ("Self -effi cacy")."""
    out = []
    for ch in name:
        out.append(r"[\s\-]*" if ch in " -" else re.escape(ch) + r"\s*")
    return "".join(out)


_COMPETENCY_NAMES = list(COMPETENCY_CODES)
COMPETENCY_RE = re.compile(
    r"(?i)(?<![a-z])(" + "|".join(_spaced(n) for n in _COMPETENCY_NAMES) + r")\s*:"
)


def _competency_code(matched: str) -> str | None:
    squashed = re.sub(r"[\s\-]+", "", matched.lower())
    for name, code in COMPETENCY_CODES.items():
        if re.sub(r"[\s\-]+", "", name) == squashed:
            return code
    return None
STRAND_RE = re.compile(r"^\s*STRAND\s+(\d+\.\d+)\s*:\s*(.+?)\s*$", re.IGNORECASE)
ROW_RE = re.compile(r"^\s*(\d+\.\d+)\s+(\d+\.\d+)\b")
LESSONS_RE = re.compile(r"\(\s*(\d+)\s*l\s*e\s*s\s*s\s*o\s*n\s*s?\s*\)", re.IGNORECASE)
OUTCOME_RE = re.compile(r"^([a-z])\)\s*(.*)$")
QUESTION_NUMBER_RE = re.compile(r"^(?:\d+\.\s*)+(.*)$")
PARAGRAPH_LABELS = [
    ("competencies", re.compile(r"(?i)^core\s+compet\w*\s+to\s+be\s+developed\s*:*\s*(.*)$")),
    ("values", re.compile(r"(?i)^values\s*:*\s*(.*)$")),
    ("pcis", re.compile(r"(?i)^pertinent\s+and\s+contemporary\s+issues\s*(?:\(pcis\))?\s*:*\s*(.*)$")),
    ("links", re.compile(r"(?i)^links?\s+to\s+other\s+learning\s+areas?\s*:*\s*(.*)$")),
]
LABELLED_RE = re.compile(r"^([A-Z][A-Za-z'\-]*(?: [A-Za-z'\-]+){0,3})\s*:\s*(.+)$")
RUBRIC_LABEL_RE = re.compile(r"(?i)^suggested assessment rubric\s*$")
END_RE = re.compile(r"(?i)^\s*appendi(?:x|ces)\b")


class PageLike(Protocol):
    pdf_page: int
    printed_page: str | None
    text: str


@dataclass
class ParsedSubStrand:
    number: str = ""
    name: str = ""
    suggested_lessons: int | None = None
    topics: list[str] = field(default_factory=list)
    outcomes: list[tuple[str | None, str]] = field(default_factory=list)
    experiences: list[str] = field(default_factory=list)
    questions: list[str] = field(default_factory=list)
    competencies: list[tuple[str, str]] = field(default_factory=list)
    values: list[tuple[str, str]] = field(default_factory=list)
    pcis: list[tuple[str, str]] = field(default_factory=list)
    link_to_other_areas: str | None = None
    first_page: int = 0
    last_page: int = 0
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # text the parser could not place


@dataclass
class ParsedRubricRow:
    indicator: str
    exceeds: str
    meets: str
    approaches: str
    below: str


@dataclass
class ParsedStrand:
    number: str
    name: str
    first_page: int
    sub_strands: list[ParsedSubStrand] = field(default_factory=list)
    rubric: list[ParsedRubricRow] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


@dataclass
class ParsedDesign:
    strands: list[ParsedStrand] = field(default_factory=list)

    def all_warnings(self) -> list[str]:
        out = []
        for st in self.strands:
            out += [f"strand {st.number}: {w}" for w in st.warnings]
            for sub in st.sub_strands:
                out += [f"{sub.number}: {w}" for w in sub.warnings]
        return out


def join_text(parts: list[str]) -> str:
    """Join wrapped lines; a line ending in a hyphen is joined without a space."""
    out = ""
    for part in (p.strip() for p in parts):
        if not part:
            continue
        if not out:
            out = part
        elif out.endswith("-") and not out.endswith(" -"):
            out += part
        else:
            out += " " + part
    return out


# ---------- column geometry ----------

def _table_bounds(header_lines: list[str], body_lines: list[str] | tuple = ()) -> list[int] | None:
    sub = spec = exp = None
    kiq_candidates: list[int] = []
    for line in header_lines:
        m = re.search(r"\bSub", line)  # the header may read "Sub-" with "Strand" on the next line
        if m and sub is None:
            sub = m.start()
        i = line.find("Specific")
        if i >= 0 and spec is None:
            spec = i
        for m in re.finditer(r"Suggested", line):
            tail = line[m.end(): m.end() + 12]
            if re.match(r"\s*Key", tail):
                kiq_candidates.append(m.start())
            elif re.match(r"\s*Learning", tail) and exp is None:
                exp = m.start()
        for word in ("Key", "Inquiry"):
            j = line.find(word)
            if j >= 0:
                kiq_candidates.append(j)
    if exp is None and spec is not None:  # header unclear: use where the experience bullets sit
        found = [mm.start() for ln in body_lines for mm in re.finditer("[\u2022\u25cf]", ln) if mm.start() > spec + 20]
        exp = min(found) if found else None
    kiq = min((k for k in kiq_candidates if exp is not None and k > exp + 10), default=None)
    if None in (sub, spec, exp, kiq):
        return None
    bounds = [sub - 7, spec - 1, exp - 2, kiq - 2]
    return bounds if bounds == sorted(set(bounds)) else None


def _is_header_line(line: str) -> bool:
    """A line of a table header (case-sensitive on purpose: running text says "sub-strand")."""
    return bool(re.search(r"Specific\s+Learning|Sub\s*-|Sub\s*Strand|Suggested\s+(?:Learning|Key)", line))


def _header_start(texts: list[str], row_index: int) -> int | None:
    for i in range(max(0, row_index - 10), row_index):
        if _is_header_line(texts[i]):
            return i
    return None


# ---------- table block ----------

def _split_columns(lines: list[str], bounds: list[int]) -> list[list[str]]:
    """Cut each line at the column boundaries. Column 3 (experiences) keeps its indentation so
    nested dashes can be told apart from primary bullets."""
    cols: list[list[str]] = [[], [], [], [], []]
    for line in lines:
        padded = line.ljust(bounds[3] + 1)
        parts = [padded[: bounds[0]], padded[bounds[0]: bounds[1]], padded[bounds[1]: bounds[2]],
                 padded[bounds[2]: bounds[3]], padded[bounds[3]:]]
        for k, part in enumerate(parts):
            if k == 3:
                # a long outcome line can spill a few characters into this cell; start at the bullet
                spill = re.search("[\u2022\u25cf\u25aa]", part[:6])
                if spill and part[: spill.start()].strip():
                    part = part[spill.start():]
            if part.strip():
                cols[k].append(part.rstrip() if k == 3 else part.strip())
    return cols


def _outcomes(lines: list[str], sub: ParsedSubStrand) -> None:
    items: list[list] = []
    for line in lines:
        m = OUTCOME_RE.match(line)
        if m:
            items.append([m.group(1), [m.group(2)]])
        elif items:
            items[-1][1].append(line)
    expected = ord("a")
    letters = []
    for code, parts in items:
        text = join_text(parts)
        while (nested := OUTCOME_RE.match(text)) is not None:  # stray "a) g) ..." markers
            code, text = nested.group(1), nested.group(2).strip()
        letters.append(code)
        if text:
            sub.outcomes.append((code, text))
    if not sub.outcomes:
        sub.warnings.append("no learning outcomes found")
    elif letters != [chr(expected + i) for i in range(len(letters))]:
        sub.warnings.append("outcome letters are not a, b, c...: " + ",".join(letters))


DOTS = "\u2022\u25cf\u25aa*"
DASHES = "-\u2013\u2014"


def _experiences(lines: list[str], sub: ParsedSubStrand) -> None:
    has_dots = any(ln.lstrip()[0] in DOTS for ln in lines)
    dash_indents = [len(ln) - len(ln.lstrip()) for ln in lines if ln.lstrip()[0] in DASHES]
    primary_indent = min(dash_indents) if dash_indents else 0
    items: list[dict] = []  # {"main": [parts], "nested": [[parts], ...]}
    target: list[str] | None = None
    for raw in lines:
        text = raw.strip()
        indent = len(raw) - len(raw.lstrip())
        char = text[0]
        if char in DOTS or (char in DASHES and not has_dots and indent <= primary_indent + 3):
            items.append({"main": [text[1:].strip()], "nested": []})
            target = items[-1]["main"]
        elif char in DASHES:
            if not items:
                items.append({"main": [], "nested": []})
            items[-1]["nested"].append([text[1:].strip()])
            target = items[-1]["nested"][-1]
        elif target is not None:
            target.append(text)
    for item in items:
        text = join_text(item["main"])
        for nested in item["nested"]:
            text += "\n- " + join_text(nested)
        if text.strip():
            sub.experiences.append(text.strip())
        if len(item["nested"]) > 3:
            sub.warnings.append("an experience has many nested dashes; check the bullet levels")
    if not sub.experiences:
        sub.warnings.append("no learning experiences found")


def _questions(lines: list[str], sub: ParsedSubStrand) -> None:
    items: list[str] = []
    numbered = False
    for line in lines:
        m = QUESTION_NUMBER_RE.match(line)
        if m:
            numbered = True
            items.append(m.group(1))
        elif items:
            items[-1] = join_text([items[-1], line])
        else:
            items.append(line)
    if len(items) == 1 and not numbered and items[0].count("?") > 1:
        items = re.split(r"(?<=\?)\s+", items[0])
    sub.questions = [i.strip() for i in items if i.strip()]
    if not sub.questions:
        sub.warnings.append("no key inquiry questions found")


def _name_and_topics(lines: list[str], sub: ParsedSubStrand) -> None:
    if not lines:
        sub.warnings.append("sub-strand cell is empty")
        return
    m = re.match(r"^(\d+\.\d+)\s*(.*)$", lines[0])
    if m:
        sub.number = m.group(1)
        name_parts, rest = [m.group(2)], lines[1:]
    else:
        name_parts, rest = [], lines
    i = 0
    while i < len(rest) and not LESSONS_RE.search(rest[i]) and rest[i][0] not in "\u2022\u25cf*":
        name_parts.append(rest[i])
        i += 1
    sub.name = join_text(name_parts)
    if i < len(rest) and LESSONS_RE.search(rest[i]):
        sub.suggested_lessons = int(LESSONS_RE.search(rest[i]).group(1))
        i += 1
    else:
        sub.warnings.append("number of lessons not found")
    topic_lines = rest[i:]
    items: list[list[str]] = []
    for line in topic_lines:
        if line[0] in "\u2022\u25cf*":
            items.append([line[1:].strip()])
        elif items:
            items[-1].append(line)
    if items:
        sub.topics = [join_text(p) for p in items if join_text(p)]
    elif topic_lines:
        sub.topics = [join_text(topic_lines)]
    if not sub.name:
        sub.warnings.append("sub-strand name not found")


def _paragraphs(lines: list[str], sub: ParsedSubStrand) -> None:
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines:
        for key, rx in PARAGRAPH_LABELS:
            m = rx.match(line)
            if m:
                current = key
                sections.setdefault(key, [])
                if m.group(1):
                    sections[key].append(m.group(1))
                break
        else:
            if current:
                sections[current].append(line)

    comp_text = join_text(sections.get("competencies", []))
    matches = list(COMPETENCY_RE.finditer(comp_text))
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(comp_text)
        code = _competency_code(m.group(1))
        if code:
            sub.competencies.append((code, comp_text[m.end():end].strip()))
    if comp_text and not sub.competencies:
        sub.warnings.append("core competency text has no recognised competency name")
        sub.notes.append("Competency text: " + comp_text)
    if not comp_text:
        sub.warnings.append("no core competencies section")

    for key, target, label in (("values", sub.values, "Values"), ("pcis", sub.pcis, "PCI")):
        text = join_text(sections.get(key, []))
        if not text:
            sub.warnings.append(f"no {label} section")
            continue
        m = LABELLED_RE.match(text)
        if m:
            target.append((m.group(1).strip(), m.group(2).strip()))
        else:
            sub.warnings.append(f"{label} text has no name; reviewer must choose one")
            sub.notes.append(f"{label} text without a name: {text}")
    links = join_text(sections.get("links", []))
    sub.link_to_other_areas = links or None


def _finish_block(block: dict, strand: "ParsedStrand", fallback: list[int] | None) -> list[int]:
    sub = ParsedSubStrand(first_page=block["first_page"], last_page=block["last_page"])
    bounds = _table_bounds(block["header"], block["lines"]) or fallback
    if bounds is None:
        sub.warnings.append("could not find the table columns; using default positions")
        bounds = [14, 36, 74, 128]
    block["bounds"] = bounds
    cols = _split_columns(block["lines"], bounds)
    _name_and_topics(cols[1], sub)
    if sub.suggested_lessons is None:
        for line in block["lines"][:10]:
            m = LESSONS_RE.search(line)
            if m:
                sub.suggested_lessons = int(m.group(1))
                sub.warnings = [w for w in sub.warnings if w != "number of lessons not found"]
                break
    _outcomes(cols[2], sub)
    _experiences(cols[3], sub)
    visible = sum(ln[bounds[2]: bounds[3]].count("\u2022") for ln in block["lines"])
    if visible and visible != sum(1 for _ in sub.experiences) and not any(
        "\n- " in e for e in sub.experiences
    ):
        sub.warnings.append(f"{visible} bullets in the experiences column but {len(sub.experiences)} parsed")
    _questions(cols[4], sub)
    _paragraphs(block["para"], sub)
    if not sub.number:
        sub.warnings.append("sub-strand number not found")
    strand.sub_strands.append(sub)
    return bounds


# ---------- rubric ----------

def _rubric_bounds(line: str, bounds: dict[str, int]) -> None:
    for key in ("Exceeds", "Meets", "Approaches", "Below"):
        i = line.find(key)
        if i >= 0 and key not in bounds:
            bounds[key] = i


def _rubric_row_cells(line: str, edges: list[int]) -> list[str]:
    padded = line.ljust(edges[-1] + 1)
    cuts = [0, *edges]
    cells = [padded[cuts[i]: cuts[i + 1]] for i in range(len(cuts) - 1)] + [padded[edges[-1]:]]
    return [c.strip() for c in cells]


def _parse_rubric(lines: list[str], strand: ParsedStrand) -> None:
    header: dict[str, int] = {}
    rows: list[list[list[str]]] = []
    for line in lines:
        if len(header) < 4:
            _rubric_bounds(line, header)
            if len(header) < 4 or not line.strip():
                continue
        if len(header) < 4:
            continue
        edges = [header[k] - 3 for k in ("Exceeds", "Meets", "Approaches", "Below")]
        cells = _rubric_row_cells(line, edges)
        if re.match(r"(?i)^(level|indicator|exceeds|meets|approaches|below)\b", cells[0]) and not rows:
            continue
        if cells[0].startswith("Ability") or not rows:
            if not any(cells):
                continue
            rows.append([[c] if c else [] for c in cells])
        else:
            for k, c in enumerate(cells):
                if c:
                    rows[-1][k].append(c)
    for row in rows:
        texts = [join_text(cell) for cell in row]
        parsed = ParsedRubricRow(*texts[:5])
        if not all(texts[:5]):
            strand.warnings.append("a rubric row has an empty cell: " + parsed.indicator[:40])
        strand.rubric.append(parsed)
    if not rows:
        strand.warnings.append("no rubric rows found")


# ---------- driver ----------

def parse_design(pages: list[PageLike]) -> ParsedDesign:
    lines: list[tuple[int, str]] = []
    for p in pages:
        raw = p.text.split("\n")
        last = max((i for i, ln in enumerate(raw) if ln.strip()), default=None)
        if last is not None and p.printed_page and raw[last].strip().lower() == p.printed_page:
            raw = raw[:last]
        lines.extend((p.pdf_page, ln) for ln in raw)

    texts = [ln for _, ln in lines]
    header_lines: set[int] = set()  # table header lines belong to the NEXT table, not the previous text
    for i, t in enumerate(texts):
        if ROW_RE.match(t):
            start = _header_start(texts, i)
            if start is not None:
                header_lines.update(range(start, i))

    design = ParsedDesign()
    strand: ParsedStrand | None = None
    block: dict | None = None
    mode: str | None = None
    rubric_lines: list[str] = []
    last_bounds: list[int] | None = None

    def close_block() -> None:
        nonlocal block, last_bounds
        if block is not None and strand is not None:
            last_bounds = _finish_block(block, strand, last_bounds)
        block = None

    def close_rubric() -> None:
        nonlocal rubric_lines
        if strand is not None and rubric_lines:
            _parse_rubric(rubric_lines, strand)
        rubric_lines = []

    for index, (page, line) in enumerate(lines):
        text = line.strip()
        if not text or index in header_lines:
            continue
        if END_RE.match(line):
            close_block()
            close_rubric()
            strand, mode = None, None
            continue
        m = STRAND_RE.match(line)
        if m and not re.search(r"\.{4,}", line):
            close_block()
            close_rubric()
            strand = ParsedStrand(number=m.group(1), name=m.group(2), first_page=page)
            design.strands.append(strand)
            mode = None
            continue
        if strand is None:
            continue
        if RUBRIC_LABEL_RE.match(text):
            close_block()
            mode = "rubric"
            continue
        if mode == "rubric":
            rubric_lines.append(line)
            continue
        if ROW_RE.match(line):
            close_block()
            start = _header_start(texts, index)
            header = texts[start:index] if start is not None else []
            block = {"lines": [line], "para": [], "header": header, "bounds": None,
                     "first_page": page, "last_page": page}
            mode = "table"
            continue
        if block is None:
            continue
        block["last_page"] = page
        if mode == "table" and PARAGRAPH_LABELS[0][1].match(text):
            mode = "para"
        if mode == "table":
            block["lines"].append(line)
        else:
            block["para"].append(text)
    close_block()
    close_rubric()
    return design
