import json

from api.corpus import company_text, load_corpus


def test_company_text_uses_long_description_when_present():
    company = {
        "long_description": "  A long detailed description.  ",
        "one_liner": "short blurb",
    }
    assert company_text(company) == "A long detailed description."


def test_company_text_falls_back_to_one_liner_when_long_description_missing():
    company = {"one_liner": "  A short blurb.  "}
    assert company_text(company) == "A short blurb."


def test_company_text_falls_back_to_one_liner_when_long_description_blank():
    company = {"long_description": "   ", "one_liner": "A short blurb."}
    assert company_text(company) == "A short blurb."


def test_company_text_returns_empty_string_when_both_missing():
    company = {"name": "Acme"}
    assert company_text(company) == ""


def test_company_text_returns_empty_string_when_both_blank():
    company = {"long_description": "  ", "one_liner": "\t\n"}
    assert company_text(company) == ""


def test_company_text_does_not_raise_on_missing_keys():
    # No exception expected for a totally empty dict.
    assert company_text({}) == ""


def test_company_text_whitespace_only_long_description_falls_through():
    company = {"long_description": "\n\t  \n", "one_liner": "fallback text"}
    assert company_text(company) == "fallback text"


def test_load_corpus_filters_and_preserves_order(tmp_path):
    companies = [
        {"id": 1, "name": "Keepable One", "long_description": "Has a description."},
        {"id": 2, "name": "Droppable", "long_description": "", "one_liner": ""},
        {"id": 3, "name": "Keepable Two", "one_liner": "Has a one-liner instead."},
        {"id": 4, "name": "Droppable No Keys"},
        {"id": 5, "name": "Keepable Three", "long_description": "   ", "one_liner": "Fallback works."},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(companies))

    result = load_corpus(str(path))

    assert [c["id"] for c in result] == [1, 3, 5]


def test_load_corpus_returns_empty_list_when_all_dropped(tmp_path):
    companies = [
        {"id": 1, "long_description": "  ", "one_liner": ""},
        {"id": 2},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(companies))

    result = load_corpus(str(path))

    assert result == []


def test_load_corpus_preserves_relative_order_of_kept_companies(tmp_path):
    companies = [
        {"id": "a", "long_description": "first"},
        {"id": "b"},  # dropped
        {"id": "c", "long_description": "third"},
        {"id": "d"},  # dropped
        {"id": "e", "one_liner": "fifth"},
    ]
    path = tmp_path / "corpus.json"
    path.write_text(json.dumps(companies))

    result = load_corpus(str(path))

    assert [c["id"] for c in result] == ["a", "c", "e"]
