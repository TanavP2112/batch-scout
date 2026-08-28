from pipeline.build_canned_examples import select_canned_examples


def test_select_canned_examples_returns_entries_in_the_requested_id_order():
    golden_set = [
        {"id": "a", "idea_text": "idea a"},
        {"id": "b", "idea_text": "idea b"},
        {"id": "c", "idea_text": "idea c"},
    ]

    selected = select_canned_examples(golden_set, ["c", "a"])

    assert [e["id"] for e in selected] == ["c", "a"]


def test_select_canned_examples_raises_on_an_unknown_id():
    golden_set = [{"id": "a", "idea_text": "idea a"}]

    try:
        select_canned_examples(golden_set, ["nonexistent"])
        assert False, "expected KeyError"
    except KeyError:
        pass
