# Docs Expense Bot

Telegram bot for tracking construction project expenses and payments.

## Features

- Reads full message history from Telegram groups
- Extracts payment amounts, contractor names, dates
- Exports structured JSON reports for accounting integration
- Supports Ukrainian hryvnia (UAH) amount parsing

## Setup

```bash
pip install -r requirements.txt
```

## Usage

```bash
python bot.py <api_id> <api_hash> "Group Name"
```

On first run, you'll be prompted to authorize with your phone number.

## Output

- `output/messages.json` — all messages from the group
- `output/expenses.json` — extracted expense records with amounts

## Environment Variables

Alternatively, set these instead of command-line args:

- `TG_API_ID` — Telegram API ID
- `TG_API_HASH` — Telegram API Hash

## License

MIT
