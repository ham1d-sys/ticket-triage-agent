import logging
import re
from datetime import datetime as dt
from typing import Dict, List, Tuple

from format import strptime_format_to_iso_8601_template

logger = logging.getLogger(__name__)


class TicketValidator:
    def __init__(self, tickets: List[Dict]):
        self.tickets = tickets
        self.invalid_tickets = {}

    def add_invalid_ticket(self, ticket: List[Dict], reason: List[str]) -> None:
        """Add invalid tickets to self.invalid_tickets."""
        key = id(ticket)
        if key not in self.invalid_tickets:
            self.invalid_tickets[key] = {"content": ticket, "reason": [reason]}
        else:
            self.invalid_tickets[key]["reason"].append(reason)

    def cleanup_tickets(self) -> None:
        """Remove invalid tickets from self.tickets"""
        if self.invalid_tickets:
            invalid_ids = set(self.invalid_tickets)
            self.tickets = [ticket for ticket in self.tickets if id(ticket) not in invalid_ids]

    def ensure_expected_fields_present_and_non_empty(self, expected_fields: Tuple[str]) -> None:
        """Ensure that all expected ticket fields are present and non-empty."""
        empty_count = 0
        missing_count = 0

        for ticket in self.tickets:
            actual_fields = set(ticket.keys())
            missing_fields = set(expected_fields) - actual_fields

            if not missing_fields:
                empty_fields = set([field for field, val in ticket.items() if field in expected_fields and not val])
                if not empty_fields:
                    continue
                reason_invalid = "Empty expected field(s)."
                empty_count += 1
            else:
                reason_invalid = "Missing expected field(s)."
                missing_count += 1

            self.add_invalid_ticket(ticket, reason_invalid)

        if empty_count:
            logger.warning(f"Found {empty_count} tickets with empty field(s).")
        if missing_count:
            logger.warning(f"Found {missing_count} tickets with missing field(s).")

        self.cleanup_tickets()

    def ensure_body_in_valid_tickets_gte_3_chars(self) -> None:
        """Ensure that the body field of a ticket is greater than or equal to 3 characters."""
        lt_3_chars_count = 0

        for ticket in self.tickets:
            body = ticket.get("body").strip()
            if not len(body) >= 3:
                reason_invalid = "`body` field is under 3 characters."
                self.add_invalid_ticket(ticket, reason_invalid)
                lt_3_chars_count += 1

        if lt_3_chars_count:
            logger.warning(f"Found {lt_3_chars_count} ticket(s) whose `body` field is under 3 characters.")

    def ensure_valid_received_at_timestamp(self, expected_timestamp_format: str) -> None:
        """Ensure that the received_at field of a ticket is the expected timestamp format."""
        readable_timestamp_format = strptime_format_to_iso_8601_template(expected_timestamp_format)
        invalid_timestamp_count = 0

        for ticket in self.tickets:
            received_at = ticket.get("received_at")
            try:
                dt.strptime(received_at, expected_timestamp_format)
                continue
            except ValueError:
                reason_invalid = f"`received_at` field contains an invalid timestamp."
                self.add_invalid_ticket(ticket, reason_invalid)
                invalid_timestamp_count += 1

        if invalid_timestamp_count:
            logger.warning(
                f"Found {invalid_timestamp_count} ticket(s) whose `received_at` timestamp field does not follow the expected '{readable_timestamp_format}' format.")

    def ensure_valid_sender(self) -> None:
        """Ensure that the sender field of a ticket contains valid email address."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        invalid_sender_count = 0

        for ticket in self.tickets:
            sender = ticket.get("sender")
            if not bool(re.match(pattern, sender)):
                reason_invalid = f"`sender` field contains an invalid email address."
                self.add_invalid_ticket(ticket, reason_invalid)

        if invalid_sender_count:
            logger.warning(
                f"Found {invalid_sender_count} ticket(s) whose `sender` field doesn't match an email address' format.")
