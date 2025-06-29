from order_checker import connect_and_search
from getpass import getpass
import yaml

def load_accounts_from_config(config_path="config.yaml"):
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    return config.get("accounts", [])

def main():
    # date_str = input("Enter the date (YYYY-MM-DD): ")
    date_str = "2025-06-26"

    print("Loading accounts")
    accounts = load_accounts_from_config()

    total_alive = 0
    total_cancels = 0
    total_orders = 0

    for acc in accounts:
        email_user = acc["email"]
        email_pass = acc["password"]
        imap_server = acc["imap_server"]

        print(f"Checking email {email_user}")
        alive, cancels, orders = connect_and_search(imap_server, email_user, email_pass, date_str)
        print(f"\n{email_user} — {alive} order(s), {cancels} cancellation(s), {orders} order(s)")
        total_alive += alive
        total_cancels += cancels
        total_orders += orders

    print("\n======= TOTAL =======")
    print(f"Alive: {total_alive}")
    print(f"Total orders: {total_orders}")
    

if __name__ == "__main__":
    main()
