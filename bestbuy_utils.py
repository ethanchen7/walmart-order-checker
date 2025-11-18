import re
from bs4 import BeautifulSoup

def extract_bestbuy_order_number_from_body(msg):
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
                
    match = re.search(r"Order\s*number[:\s]+(BBY\d{2}-\d+)", body, re.IGNORECASE)
    if match:
        return match.group(1)
    return None