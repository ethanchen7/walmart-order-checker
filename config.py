from datetime import datetime

YAHOO_IMAP_SERVER = "imap.mail.yahoo.com"
GMAIL_IMAP_SERVER = "imap.gmail.com"
# Get a unique file name per run
RUN_ID = datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"alive_orders_{RUN_ID}.txt"

MODE_TO_SENDER = {
    "walmart": "walmart.com",
    "bestbuy": "Best Buy Notifications",
    "apple": ["Apple"],
    "coin": "The United States Mint"
}

MODE_TO_KEYWORDS = {
    "walmart": ["thanks for your", "canceled", "cancellation"],
    "bestbuy": ["thanks for your", "cancelled", "cancellation"],
    "apple": ["We're processing your order", "Information about your order", "Updated information about your order"],
    "coin": ["Your U.S. Mint order has been confirmed!", "Items in your order"]
}