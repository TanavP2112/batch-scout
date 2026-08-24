from itertools import islice
from types import SimpleNamespace

from api.anthropic_batch import (
    collect_batch_results,
    parse_batch_result,
    poll_delays,
    watch_until_ended,
)


def _succeeded_result(custom_id, payload_json, stop_reason="end_turn"):
    return SimpleNamespace(
        custom_id=custom_id,
        result=SimpleNamespace(
            type="succeeded",
            message=SimpleNamespace(
                stop_reason=stop_reason,
                content=[SimpleNamespace(type="text", text=payload_json)],
            ),
        ),
    )


def _errored_result(custom_id, error_type="errored"):
    return SimpleNamespace(custom_id=custom_id, result=SimpleNamespace(type=error_type))


def test_parse_batch_result_succeeded_returns_parsed_payload():
    result = _succeeded_result("1", '{"a": 1}')
    custom_id, payload, error = parse_batch_result(result)
    assert custom_id == "1"
    assert payload == {"a": 1}
    assert error is None


def test_parse_batch_result_errored_returns_error_reason():
    result = _errored_result("2", error_type="expired")
    custom_id, payload, error = parse_batch_result(result)
    assert custom_id == "2"
    assert payload is None
    assert error == "expired"


def test_parse_batch_result_refusal_is_treated_as_error():
    result = _succeeded_result("3", "{}", stop_reason="refusal")
    _, payload, error = parse_batch_result(result)
    assert payload is None
    assert error == "refusal"


def test_parse_batch_result_missing_text_block_is_treated_as_error():
    result = SimpleNamespace(
        custom_id="4",
        result=SimpleNamespace(type="succeeded", message=SimpleNamespace(stop_reason="end_turn", content=[])),
    )
    _, payload, error = parse_batch_result(result)
    assert payload is None
    assert error == "no_text_block"


def test_collect_batch_results_splits_successes_and_errors():
    results = [
        _succeeded_result("1", '{"a": 1}'),
        _errored_result("2", error_type="canceled"),
        _succeeded_result("3", '{"b": 2}'),
    ]
    payloads, errors = collect_batch_results(results)
    assert payloads == {"1": {"a": 1}, "3": {"b": 2}}
    assert errors == {"2": "canceled"}


def test_poll_delays_is_constant():
    assert list(islice(poll_delays(), 4)) == [30, 30, 30, 30]


def test_watch_until_ended_returns_immediately_when_already_ended():
    ended_status = SimpleNamespace(processing_status="ended")
    sleeps = []

    result = watch_until_ended(retrieve_status=lambda: ended_status, sleep=sleeps.append, delays=iter([]))

    assert result is ended_status
    assert sleeps == []


def test_watch_until_ended_sleeps_and_retries_until_ended():
    statuses = iter(
        [
            SimpleNamespace(processing_status="in_progress"),
            SimpleNamespace(processing_status="in_progress"),
            SimpleNamespace(processing_status="ended"),
        ]
    )
    sleeps = []

    result = watch_until_ended(retrieve_status=lambda: next(statuses), sleep=sleeps.append, delays=iter([30, 30, 30]))

    assert result.processing_status == "ended"
    assert sleeps == [30, 30]
