import imaplib
import email
import re
from datetime import datetime
from email.header import decode_header
from datetime import datetime
from bs4 import BeautifulSoup


# Get a unique file name per run
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"alive_orders_{RUN_ID}.txt"

def write_to_file(alive_orders, email_user):
    with open(OUTPUT_FILE, "a") as f:
        for order in alive_orders:
            f.write(f"{email_user};{order}\n")


def extract_order_number_from_cancel_subject(subject):
    match = re.search(r"order\s+#(\d{15})", subject.lower())
    if match:
        return match.group(1)
    return None

def extract_order_number_from_body(msg):
    body = ""

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                payload = part.get_payload(decode=True)
                if payload:
                    body += payload.decode(errors="ignore")

            elif part.get_content_type() == "text/html":
                payload = part.get_payload(decode=True)
                if payload:
                    html = payload.decode(errors="ignore")
                    soup = BeautifulSoup(html, "html.parser")
                    body += soup.get_text()

    else:
        if msg.get_content_type() == "text/html":
            payload = msg.get_payload(decode=True)
            if payload:
                html = payload.decode(errors="ignore")
                soup = BeautifulSoup(html, "html.parser")
                body = soup.get_text()

    match = re.search(r"Order number:\s+(\d{7}-\d{8})", body)
    if match:
        return match.group(1)
    return None



def connect_and_search(imap_server, email_user, email_pass, date_str):
    date_formatted = datetime.strptime(date_str, "%Y-%m-%d").strftime("%d-%b-%Y")
    # Gmail: INBOX, Gmail/Spam
    # Yahoo: INBOX, Bulk
    folders_to_check = ['INBOX', '[Gmail]/Spam', 'Bulk']

    confirmed_orders = set()
    cancelled_orders = set()

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)

        for folder in folders_to_check:
            try:
                mail.select(folder)
                typ, msg_ids = mail.search(None, f'(ON "{date_formatted}" FROM "walmart.com")')
                if typ != 'OK':
                    continue

                for num in msg_ids[0].split():
                    typ, data = mail.fetch(num, '(RFC822)')
                    if typ != 'OK':
                        continue

                    msg = email.message_from_bytes(data[0][1])
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding or "utf-8")

                    if "thanks for your" in subject:
                        order_number = extract_order_number_from_body(msg)
                        print(order_number)
                        if order_number:
                            confirmed_orders.add(order_number)
                    elif "canceled" in subject.lower():
                        flat_order_number = extract_order_number_from_cancel_subject(subject)
                        if flat_order_number:
                            cancelled_orders.add(flat_order_number)

            except Exception as e:
                print(f"Error checking folder {folder}: {e}")

        mail.logout()

    except Exception as e:
        print(f"Failed to check {email_user}: {e}")

    # Match normalized order numbers (remove dashes)
    alive_orders = [
        o for o in confirmed_orders
        if o.replace("-", "") not in cancelled_orders
    ]

    write_to_file(alive_orders, email_user)

    return len(alive_orders), len(cancelled_orders), len(confirmed_orders)

