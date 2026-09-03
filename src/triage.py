import logging
from pathlib import Path

from tenacity import RetryError

from ticket_io import load_support_tickets, write_invalid_tickets
from process import TriageProcessor
from validate import TicketValidator

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(pathname)s - %(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

EXPECTED_FIELDS = ("sender", "subject", "body", "received_at")
EXPECTED_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
support_tickets_path = Path(__file__).resolve().parent.parent / "data" / "input" / "support_tickets.csv"
output_path = Path(__file__).resolve().parent.parent / "data" / "output"


def main():
    support_tickets = load_support_tickets(support_tickets_path)

    ticket_validator = TicketValidator(support_tickets)
    ticket_validator.ensure_expected_fields_present_and_non_empty(EXPECTED_FIELDS)
    ticket_validator.ensure_body_in_valid_tickets_gte_3_chars()
    ticket_validator.ensure_valid_received_at_timestamp(EXPECTED_TIMESTAMP_FORMAT)
    ticket_validator.ensure_valid_sender()
    ticket_validator.cleanup_tickets()
    valid_tickets = ticket_validator.tickets
    invalid_tickets = ticket_validator.invalid_tickets

    triage_processor = TriageProcessor(valid_tickets, output_path)
    try:
        triage_processor.process_tickets()
    except RetryError as e:
        logger.warning(f"{e.__name__}: {e}. Batch aborted.")
        return

    invalid_tickets_header = ["content", "reason"]
    write_invalid_tickets(invalid_tickets, invalid_tickets_header, output_path)
    triage_processor.write_outputs()


if __name__ == "__main__":
    main()
