from app.importer.design_parser import join_text, parse_design
from tests.layout_fixtures import PAGES


def test_contents_page_lines_are_not_mistaken_for_strands():
    design = parse_design(PAGES)
    assert [(s.number, s.name) for s in design.strands] == [("1.0", "DEMO STRAND"), ("2.0", "SECOND DEMO STRAND")]


def test_first_sub_strand_is_read_column_by_column():
    first = parse_design(PAGES).strands[0].sub_strands[0]
    assert first.number == "1.1"
    assert first.name == "Demo Numbers"
    assert first.suggested_lessons == 20
    assert first.topics == ["Demo topic"]
    assert first.outcomes == [
        ("a", "demo outcome one,"),
        ("b", "demo outcome two that wraps to the next line,"),
        ("c", "appreciate demo"),
    ]
    assert first.experiences == [
        "demo experience one continues here",
        "demo experience two with a hyphen-ated word",
    ]
    assert first.questions == ["What is a demo?", "Why demo?"]
    assert (first.first_page, first.last_page) == (13, 13)


def test_paragraph_sections_are_split_into_competencies_values_pcis_and_links():
    first = parse_design(PAGES).strands[0].sub_strands[0]
    assert first.competencies == [("critical_thinking", "learner does a demo.")]
    assert first.values == [("Unity", "learner works together.")]
    assert first.pcis == []  # no name given: flagged, not guessed
    assert any("PCI text has no name" in w for w in first.warnings)
    assert any("Learner does something safely." in n for n in first.notes)
    assert first.link_to_other_areas == "Learner links demo to Creative Arts."


def test_each_table_uses_its_own_column_positions():
    second = parse_design(PAGES).strands[0].sub_strands[1]
    assert second.number == "1.2" and second.name == "Second"
    assert [o[0] for o in second.outcomes] == ["a", "b"]
    assert second.experiences == ["second experience", "another experience"]
    assert second.questions == ["How do we do the second?"]
    assert second.pcis == [("Safety", "learner stays safe.")]


def test_kerned_text_is_tolerated():
    second = parse_design(PAGES).strands[0].sub_strands[1]
    assert second.suggested_lessons == 6
    assert second.competencies == [("self_efficacy", "learner is confident.")]


def test_rubric_rows_are_split_by_level_and_wrapped_cells_are_joined():
    rubric = parse_design(PAGES).strands[0].rubric
    assert len(rubric) == 2
    assert rubric[0].indicator == "Ability to demo one thing"
    assert rubric[0].exceeds == "Demo exceeds wraps"
    assert rubric[0].below == "Demo below here"
    assert rubric[1].meets == "Two meets"


def test_parsing_stops_at_the_appendices_and_handles_several_strands():
    design = parse_design(PAGES)
    assert len(design.strands) == 2
    third = design.strands[1].sub_strands[0]
    assert third.number == "2.1" and third.suggested_lessons == 5
    assert third.competencies == [("citizenship", "learner votes.")]


def test_text_that_is_not_a_design_produces_nothing():
    class P:
        pdf_page, printed_page, text = 1, None, "Just an ordinary page\nwith nothing to parse."

    assert parse_design([P()]).strands == []


def test_join_text_handles_hyphenated_line_breaks():
    assert join_text(["a 4-", "digit number"]) == "a 4-digit number"
    assert join_text(["one", "", "two"]) == "one two"
