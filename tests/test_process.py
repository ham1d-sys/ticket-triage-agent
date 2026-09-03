from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter, wait_none

from process import TriageProcessor, initial_wait, max_wait, stop_count

test_tickets = [{
    "sender": "maria.k@example.com",
    "subject": "Can't log in",
    "body": "I get invalid credentials every time I try.",
    "received_at": "2026-08-19 07:12:00"
}, ]


@retry(
    wait=wait_exponential_jitter(initial=initial_wait, max=max_wait),
    stop=stop_after_attempt(stop_count),
    retry=retry_if_exception_type(APIConnectionError),
    reraise=True,
)
def make_response_output(refusal: bool = False, fail: bool = False) -> MagicMock | None:
    """
    Create a mock response or raise an exception.
    :param refusal: Whether to create a refusal response.
    :param fail: Whether to raise an exception.
    :return: A MagicMock response unless an exception is raised.
    """
    if fail:
        raise APIConnectionError(
            request=MagicMock()
        )
    content_item = MagicMock()
    content_item.type = "refusal" if refusal else "output_text"
    output = MagicMock()
    output.type = "message"
    output.content = [content_item]
    response = MagicMock()
    response.output = [output]
    return response


@patch("process.client")
def test_process_tickets_retry_on_transient_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure process_tickets() retries after transient API connection errors."""
    monkeypatch.setattr(
        make_response_output.retry, "stop", stop_after_attempt(3)
    )
    monkeypatch.setattr(make_response_output.retry, "wait", wait_none())
    with pytest.raises(APIConnectionError):
        make_response_output(fail=True)

    stats = make_response_output.statistics
    assert "attempt_number" in stats
    assert stats["attempt_number"] == stop_count


@patch("process.client")
def test_process_tickets_handles_refusal_response(mock_client: MagicMock):
    """Ensure refused tickets are added to needs_review with the correct reason."""
    mock_client.responses.parse.return_value = make_response_output(refusal=True)
    triage_processor = TriageProcessor(test_tickets, "some path")
    triage_processor.process_tickets()
    assert triage_processor.needs_review[0]["reason"] == "Refusal."
