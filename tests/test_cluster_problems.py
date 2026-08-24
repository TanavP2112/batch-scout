from pipeline.cluster_problems import merge_problem_labels


def test_merge_problem_labels_rewrites_value_and_keeps_span():
    raw = {
        "1": {
            "customer": {"value": "SMB", "span": "x"},
            "problem": {"value": "raw-label", "span": "manual expense reports"},
        }
    }
    merged = merge_problem_labels(raw, {"1": "expense-report-automation"})
    assert merged["1"]["problem"] == {"value": "expense-report-automation", "span": "manual expense reports"}
    assert merged["1"]["customer"] == {"value": "SMB", "span": "x"}  # untouched


def test_merge_problem_labels_does_not_mutate_input():
    raw = {"1": {"problem": {"value": "raw-label", "span": "s"}}}
    merge_problem_labels(raw, {"1": "new-label"})
    assert raw["1"]["problem"]["value"] == "raw-label"
