import re
from bs4 import BeautifulSoup


def extract_coin_order_number_from_subject(subject):
    match = re.search(r"items in your order ([A-Z]+\d+)", subject, re.IGNORECASE)
    if match:
        print(f"cancel match, {match.group(1)}")
        return match.group(1)
    return None

def extract_coin_order_number_from_body(msg):
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

    match = re.search(r"your\s+order\s*#\s*([A-Z]+\d+)", body, re.IGNORECASE)
    if match:
        print(f"order match, {match.group(1)}")
        return match.group(1)
    return None