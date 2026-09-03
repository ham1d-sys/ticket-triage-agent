import csv
import os
from logging import getLogger
from pathlib import Path
from typing import List, Dict

from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APITimeoutError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter, RetryError

logger = getLogger(__name__)
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(
    api_key=api_key,
    timeout=900.0,
)

initial_wait = 1
max_wait = 10
stop_count = 4


class Classification(BaseModel):
    """Define JSON output schema"""
    category: str
    urgency: str
    reason: str


class TriageProcessor:
    """Triage tickets."""

    def __init__(self, tickets: List[Dict], output_path: Path):
        self.tickets = tickets
        self.triaged = []
        self.needs_review = []
        self.output_path = output_path

    @retry(
        retry=retry_if_exception_type((APIConnectionError, APITimeoutError)),
        wait=wait_exponential_jitter(initial=initial_wait, max=max_wait),
        stop=stop_after_attempt(stop_count),
        reraise=True,
    )
    def process_tickets(self) -> None:
        """Classify tickets using the OpenAI API."""
        unclassified_count = 0
        rows_status = []

        for ticket in self.tickets:
            try:
                response = client.responses.parse(
                    model="gpt-5.6-luna",
                    input=[
                        {
                            "role": "system",
                            "content": "You're a support ticket triage assistant. Classify this support ticket into a category (billing / bug / feature_request / spam / other) and an urgency (low / medium / high) with a concise one-line reason.",
                        },
                        {
                            "role": "user",
                            "content": f"{ticket}",
                        },
                    ],
                    text_format=Classification,
                    service_tier="flex",
                )
                for output in response.output:
                    if output.type != "message":
                        continue

                    for item in output.content:
                        if item.type == "refusal":
                            unclassified_count += 1
                            self.needs_review.append({"content": ticket, "reason": "Refusal."})
                            continue

                        self.triaged.append({"content": ticket, **response.output_parsed.model_dump()})
                        rows_status.append(True)
            except (APIConnectionError, APITimeoutError) as e:
                self.needs_review.append(
                    {"content": ticket, "reason": f"{e.__name__} after {stop_count} triage attempts."})
                if len(rows_status) > stop_count and not any(
                        [i for n, i in enumerate(rows_status, start=1) if n >= (len(rows_status) - stop_count)]):
                    raise RetryError(f"Hit {stop_count} consecutive API connection or timeout errors")
                continue

        if unclassified_count:
            logger.warning(f"{unclassified_count} tickets couldn't be classified. Review them in `needs_review.csv`.")

    def write_outputs(self) -> None:
        """Write self.needs_review and self.triaged to needs_review.csv and triaged.csv, respectively"""
        if self.needs_review:
            needs_review_path = self.output_path / "needs_review.csv"
            with open(needs_review_path, "w", encoding="UTF-8", newline="") as needs_review_file:
                fieldnames = ["content", "reason"]
                writer = csv.DictWriter(needs_review_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.needs_review)
            logger.info(f"Wrote needs-review tickets to '{needs_review_path}'")

        if self.triaged:
            triaged_path = self.output_path / "triaged.csv"
            with open(triaged_path, "w", encoding="UTF-8", newline="") as triaged_file:
                fieldnames = ["content", "category", "urgency", "reason"]
                writer = csv.DictWriter(triaged_file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(self.triaged)
                logger.info(f"Wrote triage results to '{triaged_path}'")
