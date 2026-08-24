from eval.llm_judge import (
    build_judge_pairs,
    build_judge_request,
    coverage_report,
    judge_custom_id,
    judge_schema,
)


def test_judge_schema_requires_relevant_and_reason():
    schema = judge_schema()
    assert schema["required"] == ["relevant", "reason"]
    assert schema["properties"]["relevant"]["type"] == "boolean"
    assert schema["properties"]["reason"]["type"] == "string"
    assert schema["additionalProperties"] is False


def test_judge_custom_id_joins_query_and_company_id():
    assert judge_custom_id("idea-1", 572) == "idea-1::572"


def test_build_judge_request_uses_judge_custom_id():
    company = {"id": 572, "name": "Abacus", "long_description": "expense management"}
    request = build_judge_request("idea-1", "expense tracking for teams", company)
    assert request["custom_id"] == "idea-1::572"


def test_build_judge_request_includes_idea_text_and_company_text():
    company = {"id": 572, "name": "Abacus", "long_description": "expense management"}
    request = build_judge_request("idea-1", "expense tracking for teams", company)
    content = request["params"]["messages"][0]["content"]
    assert "expense tracking for teams" in content
    assert "Abacus" in content
    assert "expense management" in content


def test_build_judge_pairs_takes_top_depth_per_query_in_run_order():
    # run's dict order is the rank order build_run already produces — no re-sort needed.
    run = {"idea-1": {"c0": 0.9, "c1": 0.5, "c2": 0.1}}
    pairs = build_judge_pairs(run, depth=2)
    assert pairs == [("idea-1", "c0"), ("idea-1", "c1")]


def test_build_judge_pairs_covers_every_query():
    run = {"idea-1": {"c0": 0.9}, "idea-2": {"c1": 0.5}}
    pairs = build_judge_pairs(run, depth=10)
    assert set(pairs) == {("idea-1", "c0"), ("idea-2", "c1")}


def test_coverage_report_counts_judged_relevant():
    judgments = {
        "idea-1::572": {"relevant": True, "reason": "x"},
        "idea-1::999": {"relevant": False, "reason": "y"},
    }
    qrels = {"idea-1": {"572": 1}}

    report = coverage_report(judgments, qrels)

    assert report["idea-1"]["judged_relevant"] == 1


def test_coverage_report_flags_judged_relevant_pairs_missing_from_qrels():
    judgments = {
        "idea-1::572": {"relevant": True, "reason": "x"},
        "idea-1::999": {"relevant": True, "reason": "y"},
    }
    qrels = {"idea-1": {"572": 1}}  # 999 judged relevant but absent from qrels — a candidate false negative

    report = coverage_report(judgments, qrels)

    assert report["idea-1"]["judged_relevant_not_in_qrels"] == ["999"]


def test_coverage_report_handles_query_with_no_qrels_entry():
    judgments = {"idea-2::1": {"relevant": True, "reason": "x"}}
    qrels = {}  # idea-2 has zero labeled relevant companies (a legitimate whitespace label)

    report = coverage_report(judgments, qrels)

    assert report["idea-2"]["judged_relevant_not_in_qrels"] == ["1"]
