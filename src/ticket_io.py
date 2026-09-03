import csv
from logging import getLogger

logger = getLogger(__name__)

def load_support_tickets(tickets_path):
    with open(tickets_path, "r", encoding='UTF-8', newline='') as tickets_file:
        tickets = list(
            csv.DictReader(tickets_file)
        )
        logger.info(f"Loaded tickets from '{tickets_path}'.")
    return tickets

def write_invalid_tickets(invalid_tickets, fieldnames, output_path):
    if invalid_tickets:
        invalid_tickets_path = output_path / "invalid_tickets.csv"
        with open(invalid_tickets_path, "w", encoding='UTF-8', newline='') as invalid_tickets_file:
            writer = csv.DictWriter(invalid_tickets_file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(invalid_tickets.values())
            logger.info(f"Wrote invalid tickets to '{invalid_tickets_path}'.")