# Walmart Order Checker

Parses messages in inboxes for Walmart orders that have survived cancels and outputs file with order numbers.

### Usage

Fill out `config.yaml` with IMAP configurations. Password is app password, not your actual email password.

Run the following:

```
## optional, setup virtual environment
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

python3 main.py
```

### IMAP Settings

- Gmail: `imap.gmail.com`

- Yahoo: `imap.mail.yahoo.com`