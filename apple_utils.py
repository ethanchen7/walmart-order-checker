import re
from bs4 import BeautifulSoup

def extract_apple_order_info(msg):
    body = ""
    product_name = None
    order_number = None
    order_status = "Alive"
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

                # Extract product names from <td>
                for td in soup.find_all("td"):
                    text = td.get_text(strip=True)
                    if text:  
                        # Optional: filter to look like product names
                        if re.search(r"iPhone|MacBook|iPad|Watch|AirPods", text, re.I):
                            product_name_match = re.search(
                                r"((?:iPhone|MacBook|iPad|Watch|AirPods)\s.+?)(?=Carrier:|\$|\n|Pickup Date:)",
                                text,
                                re.DOTALL | re.IGNORECASE
                            )
                            if product_name_match:
                                product_name = product_name_match.group(1).strip()
                        
                        order_number_match = re.search(r"Order Number:\s*([A-Z]\d+)", text)
                        if order_number_match:
                            order_number = order_number_match.group(1).strip()

                        delivery_match = re.search(r"Delivers:\s*([A-Za-z]{3}\s\d{1,2})\s*[-–]\s*([A-Za-z]{3}\s\d{1,2})", text)
                        if delivery_match:
                            order_status = f"Delivers: {delivery_match.group(1)} - {delivery_match.group(2)}"
        
        cancelled_match = re.search(r"your order has been cancelled", body, re.I)
        order_status_match = re.search(r"Delivers:\s*([A-Za-z]{3}\s\d{1,2})\s*[-–]\s*([A-Za-z]{3}\s\d{1,2})", body)
        if cancelled_match:
            order_status = "Cancelled"
        elif order_status_match:
            order_status = f"Delivers: {order_status_match.group(1)} - {order_status_match.group(2)}"                        
    
    return product_name, order_number, order_status
