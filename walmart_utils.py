import re
from bs4 import BeautifulSoup


def extract_walmart_order_number_from_subject(subject):
    match = re.search(r"order\s+#(\d{15})", subject.lower())
    if match:
        return match.group(1)
    return None

def extract_walmart_order_number_from_body(msg):
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