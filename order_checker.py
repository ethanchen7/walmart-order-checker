import imaplib
import email
import re
from datetime import datetime
from email.header import decode_header
from datetime import datetime
from bs4 import BeautifulSoup

YAHOO_IMAP_SERVER = "imap.mail.yahoo.com"
GMAIL_IMAP_SERVER = "imap.gmail.com"
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
    gmail_folders_to_check = ['INBOX', '[Gmail]/Spam']
    yahoo_folders_to_check = ['INBOX', 'Bulk']

    confirmed_orders = set()
    cancelled_orders = set()

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        mail.login(email_user, email_pass)

        subject_keywords = [
            "thanks for your",
            "canceled"
        ]

        folders_to_check = yahoo_folders_to_check if imap_server == YAHOO_IMAP_SERVER else gmail_folders_to_check

        for folder in folders_to_check:
            try:
                mail.select(folder)

                for keyword in subject_keywords:
                    # Use SUBJECT filter to narrow search
                    search_criteria = f'(ON "{date_formatted}" FROM "walmart.com" SUBJECT "{keyword}")'
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

                        if "thanks for your" in subject.lower():
                            typ, data = mail.fetch(num, '(RFC822)')
                            if typ != 'OK':
                                continue
                            msg = email.message_from_bytes(data[0][1])
                            order_number = extract_order_number_from_body(msg)
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
    
    print("\n-------- Alive Orders: --------")
    print(alive_orders)

    write_to_file(alive_orders, email_user)

    return len(alive_orders), len(cancelled_orders)

