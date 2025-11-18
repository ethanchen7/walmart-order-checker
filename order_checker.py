from collections import defaultdict
import imaplib
import email
from datetime import datetime
from email.header import decode_header
from datetime import datetime

from apple_utils import extract_apple_order_info
from coin_utils import extract_coin_order_number_from_body, extract_coin_order_number_from_subject
from config import MODE_TO_KEYWORDS, MODE_TO_SENDER, OUTPUT_FILE, YAHOO_IMAP_SERVER
from bestbuy_utils import extract_bestbuy_order_number_from_body
from walmart_utils import extract_walmart_order_number_from_body, extract_walmart_order_number_from_subject

def write_to_file(alive_orders, email_user):
    with open(OUTPUT_FILE, "a") as f:
        for order in alive_orders:
            f.write(f"{email_user};{order}\n")

def apple_write_to_file(email_to_item_name):
    print(email_to_item_name)
    with open(OUTPUT_FILE, "a") as f:
        for email in email_to_item_name:
            for item_name in email_to_item_name[email]:
                for order_number in email_to_item_name[email][item_name]:
                    order_status = email_to_item_name[email][item_name][order_number]
                    f.write(f"{email};{item_name};{order_number};{order_status}\n")

def resolve_walmart_orders(subject, mail, num, confirmed_orders, cancelled_orders):
    if "thanks for your" in subject.lower():
        typ, data = mail.fetch(num, '(RFC822)')
        if typ != 'OK':
            return
        msg = email.message_from_bytes(data[0][1])
        order_number = extract_walmart_order_number_from_body(msg)
        if order_number:
            confirmed_orders.add(order_number)

    elif "canceled" in subject.lower():
        flat_order_number = extract_walmart_order_number_from_subject(subject)
        if flat_order_number:
            cancelled_orders.add(flat_order_number)

def resolve_bestbuy_orders(subject, mail, num, confirmed_orders, cancelled_orders):
    typ, data = mail.fetch(num, '(RFC822)')
    if typ != 'OK':
        return
    msg = email.message_from_bytes(data[0][1])
    if "thanks for your" in subject.lower():
        order_number = extract_bestbuy_order_number_from_body(msg)
        if order_number:
            confirmed_orders.add(order_number)
    elif "cancelled" in subject.lower() or "cancellation" in subject.lower():
        order_number = extract_bestbuy_order_number_from_body(msg)
        if order_number:
            cancelled_orders.add(order_number)
        else:
            raise Exception("No order number found in this email!")

def resolve_apple_orders(subject, mail, num, email_to_item_name):
    typ, data = mail.fetch(num, '(RFC822)')
    if typ != 'OK':
        return
    msg = email.message_from_bytes(data[0][1])
    recipient = msg.get('To', '')
    item_name, order_number, order_status = extract_apple_order_info(msg)
    email_to_item_name[recipient] = {
        item_name: {
            order_number: order_status
        }
    }

def resolve_coin_orders(subject, mail, num, confirmed_orders, cancelled_orders):
    if "confirmed" in subject.lower():
        typ, data = mail.fetch(num, '(RFC822)')
        if typ != 'OK':
            return
        msg = email.message_from_bytes(data[0][1])
        order_number = extract_coin_order_number_from_body(msg)
        if order_number:
            confirmed_orders.add(order_number)

    elif "canceled" in subject.lower():
        flat_order_number = extract_coin_order_number_from_subject(subject)
        if flat_order_number:
            cancelled_orders.add(flat_order_number)

def get_alive_orders(confirmed_orders, cancelled_orders, mode):
    if mode == "walmart":
        return [
            o for o in confirmed_orders
            if o.replace("-", "") not in cancelled_orders
        ]
    else:
        return [
            o for o in confirmed_orders
            if o not in cancelled_orders
        ]

def connect_and_search(imap_server, email_user, email_pass, start_date_str, end_date_str, mode):
    start_date_formatted = datetime.strptime(start_date_str, "%Y-%m-%d").strftime("%d-%b-%Y")
    end_date_formatted = datetime.strptime(end_date_str, "%Y-%m-%d").strftime("%d-%b-%Y")
    # Gmail: INBOX, Gmail/Spam
    # Yahoo: INBOX, Bulk
    gmail_folders_to_check = ['INBOX', '[Gmail]/Spam']
    yahoo_folders_to_check = ['INBOX', 'Bulk']

    confirmed_orders = set()
    cancelled_orders = set()
    email_to_item_name = defaultdict()

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)

        subject_keywords = MODE_TO_KEYWORDS[mode]

        folders_to_check = yahoo_folders_to_check if imap_server == YAHOO_IMAP_SERVER else gmail_folders_to_check
        sender = MODE_TO_SENDER[mode.lower()]

        for folder in folders_to_check:
            try:
                mail.select(folder)

                for keyword in subject_keywords:
                    # Use SUBJECT filter to narrow search
                    search_criteria = f'(SINCE "{start_date_formatted}" BEFORE "{end_date_formatted}" FROM "{sender}" SUBJECT "{keyword}")'
                    typ, msg_ids = mail.search(None, search_criteria)
                    if typ != 'OK' or not msg_ids[0]:
                        continue

                    for num in msg_ids[0].split():
                        # Fetch only Subject header first to validate
                        typ, data = mail.fetch(num, '(BODY.PEEK[HEADER.FIELDS (SUBJECT)])')
                        if typ != 'OK':
                            continue

                        raw_header = data[0][1]
                        msg = email.message_from_bytes(raw_header)
                        subject, encoding = decode_header(msg["Subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding or "utf-8")

                        if mode == "walmart":
                            resolve_walmart_orders(subject, mail, num, confirmed_orders, cancelled_orders)
                        elif mode == "bestbuy":
                            resolve_bestbuy_orders(subject, mail, num, confirmed_orders, cancelled_orders)
                        elif mode == "apple":
                            resolve_apple_orders(subject, mail, num, email_to_item_name)
                        else:
                            resolve_coin_orders(subject, mail, num, confirmed_orders, cancelled_orders)

            except Exception as e:
                print(f"Error checking folder {folder}: {e}")

        mail.logout()

    except Exception as e:
        print(f"Failed to check {email_user}: {e}")

    if mode == "apple":
        apple_write_to_file(email_to_item_name)
        return len(email_to_item_name), 0
    else: 
        alive_orders = get_alive_orders(confirmed_orders, cancelled_orders, mode)
        print("\n-------- Alive Orders: --------")
        print(alive_orders)

        write_to_file(alive_orders, email_user)

        return len(alive_orders), len(cancelled_orders)

