# csv_inv_order/send_reminders.py

import os
import re
import smtplib
from datetime import date, timedelta
from email.message import EmailMessage
from csv_inv_order.database import *


def parse_notify_date(date_str, today):
    """Parse Notify date string and return target date."""
    # Clean up the string: remove spaces, make uppercase
    cleaned = re.sub(r'\s+', '', date_str).upper()
    match = re.match(r'^([EMB])([+-]\d+)?$', cleaned)
    if not match:
        raise ValueError(f"Invalid Notify date: {date_str}")

    event_type, suffix = match.groups()

    # Determine which occurrence to use and parse offset
    if suffix.startswith('+'):
        # Previous occurrence (before today), offset is positive
        base_date = find_previous_occurrence(event_type, today - timedelta(days=1))
        offset = int(suffix[1:])
    elif suffix.startswith('-'):
        # Next occurrence (on or after today), offset is negative
        base_date = find_next_occurrence(event_type, today)
        offset = -int(suffix[1:])
    else:
        # No sign: next occurrence, offset is zero
        base_date = find_next_occurrence(event_type, today)
        offset = 0

    if not base_date:
        return None

    # Apply offset
    target_date = base_date + timedelta(days=offset)

    return target_date

def find_next_occurrence(event_type, from_date):
    """Find next occurrence of event on or after from_date, within 31 days."""
    current = from_date
    for _ in range(32):  # Check up to 31 days forward
        if is_event_date(event_type, current):
            return current
        current += timedelta(days=1)
    return None

def find_previous_occurrence(event_type, from_date):
    """Find previous occurrence of event on or before from_date, within 31 days."""
    current = from_date
    for _ in range(32):  # Check up to 31 days backward
        if is_event_date(event_type, current):
            return current
        current -= timedelta(days=1)
    return None

def is_event_date(event_type, check_date):
    """Check if date matches event criteria."""
    month = check_date.month
    day = check_date.day
    weekday = check_date.weekday()  # Monday=0, Sunday=6

    if event_type == 'E':  # Executive Board Meeting: last Tue of month, Oct-Mar
        if month not in (10, 11, 12, 1, 2, 3):
            return False
        if weekday != 1:  # Tuesday
            return False
        # Check if it's the last Tuesday of the month
        next_week = check_date + timedelta(days=7)
        return next_week.month != month

    elif event_type == 'M':  # Member Meeting: first Tue of month, Nov-Apr
        if month not in (11, 12, 1, 2, 3, 4):
            return False
        if weekday != 1:  # Tuesday
            return False
        # Check if it's the first Tuesday of the month
        return day <= 7

    elif event_type == 'B':  # Breakfast: second Sat of month, Nov-Apr
        if month not in (11, 12, 1, 2, 3, 4):
            return False
        if weekday != 5:  # Saturday
            return False
        # Check if it's the second Saturday of the month
        return 8 <= day <= 14

    return False

def send_email(to_addrs, subject, body):
    """Send email via Brevo SMTP."""

    SMTP_SERVER = os.getenv("SMTP_SERVER")
    SMTP_PORT = int(os.getenv("SMTP_PORT"))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_KEY = os.getenv("SMTP_KEY")
    FROM_EMAIL = "GGmensclub@gmail.com"

    msg = EmailMessage()
    msg['From'] = FROM_EMAIL
    msg['To'] = ', '.join(to_addrs)
    msg['Subject'] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_KEY)
            server.send_message(msg)
        return True
    except Exception as e:
        raise RuntimeError(f"Failed to send email: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Send email reminders")
    parser.add_argument("--test", "-t", action="store_true", help="Test mode", default=False)
    args = parser.parse_args()
    testing = args.test

    load_database(exclusive=not testing)
    today = date.today()

    # Build step lookup: step number -> step object
    steps_by_number = {step.number: step for step in Steps.values()}

    for notify_row in Notify.values():
        # Condition 1: Step check
        if notify_row.step:
            step_number = notify_row.step.upper()
            if step_number[0] == '~':    # negates step has_run check
                step = steps_by_number[step_number[1:]]
                if not step.has_run:
                    continue
            else:
                step = steps_by_number[step_number]
                if step.has_run:
                    continue

        # Condition 2: Date calculation
        target_date = parse_notify_date(notify_row.date, today)
        if not target_date or target_date > today:
            continue

        # Condition 3: Last sent check
        last_sent = notify_row.last_sent
        if last_sent and last_sent >= target_date:
            continue

        # All conditions met - send email
        email_addrs = notify_row.email_addrs.split()
        if testing:
            print(f"Would send {notify_row.message} to {', '.join(email_addrs)}")
        else:
            if send_email(email_addrs, notify_row.subject, notify_row.message):
                notify_row.last_sent = today
                save_database()     # in case later Notify rows raise an exception



if __name__ == "__main__":
    main()
