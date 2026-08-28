import json
import pathlib
import time

from anthropic import Anthropic


def parse_batch_result(result) -> tuple[str, dict | None, str | None]:
    """Returns (custom_id, payload_or_None, error_reason_or_None) for one batch result."""
    if result.result.type != "succeeded":
        return result.custom_id, None, result.result.type

    message = result.result.message
    if message.stop_reason == "refusal":
        return result.custom_id, None, "refusal"

    text_block = next((b for b in message.content if b.type == "text"), None)
    if text_block is None:
        return result.custom_id, None, "no_text_block"

    return result.custom_id, json.loads(text_block.text), None


def collect_batch_results(results) -> tuple[dict[str, dict], dict[str, str]]:
    """Splits a batch's results into {custom_id: payload} and {custom_id: error_reason}."""
    payloads: dict[str, dict] = {}
    errors: dict[str, str] = {}
    for result in results:
        custom_id, payload, error = parse_batch_result(result)
        if error is None:
            payloads[custom_id] = payload
        else:
            errors[custom_id] = error
    return payloads, errors


def poll_delays(interval: float = 30):
    """Successive wait times between batch-status checks: a constant interval."""
    while True:
        yield interval


def watch_until_ended(retrieve_status, sleep=time.sleep, delays=None):
    delays = delays if delays is not None else poll_delays()
    status = retrieve_status()
    while status.processing_status != "ended":
        sleep(next(delays))
        status = retrieve_status()
    return status


def submit_batch(client: Anthropic, requests: list, batch_id_path: pathlib.Path) -> str:
    batch = client.messages.batches.create(requests=requests)
    batch_id_path.write_text(batch.id)
    print(f"submitted batch {batch.id} ({len(requests)} requests)")
    print(f"batch id cached at {batch_id_path}")
    return batch.id


def poll_and_collect(client: Anthropic, batch_id: str, watch: bool = False) -> tuple[dict, dict] | None:
    """Returns (results, errors) once the batch has ended, or None if not ended and not watching."""
    if watch:
        print("watching until the batch ends (checking every 30s)...")
        batch = watch_until_ended(lambda: client.messages.batches.retrieve(batch_id))
    else:
        batch = client.messages.batches.retrieve(batch_id)

    print(f"status: {batch.processing_status}  counts: {batch.request_counts}")
    if batch.processing_status != "ended":
        print("not finished yet — rerun this command later, or pass --watch")
        return None

    return collect_batch_results(client.messages.batches.results(batch_id))
