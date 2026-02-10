"""
Docs Expense Bot — Telegram bot for tracking construction expenses.
Reads group chat history, extracts payment records, invoices and expense data.
Exports structured JSON reports for accounting.
"""

import json
import re
import os
import sys
import asyncio
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument


API_ID = int(os.environ.get("TG_API_ID", 0))
API_HASH = os.environ.get("TG_API_HASH", "")
BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")

SESSION_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_FILE = os.path.join(SESSION_DIR, "tg_session")
OUTPUT_DIR = os.path.join(SESSION_DIR, "output")


def extract_amounts(text):
    """Extract monetary amounts from message text."""
    if not text:
        return []

    patterns = [
        r'(\d[\d\s]*\d)\s*(?:hrn|grn|uah|грн|грив)',
        r'(?:оплат\w*|заплат\w*|перерахув\w*|переказ\w*)\s*(\d[\d\s.,]*\d)',
        r'(\d{4,}(?:[.,]\d{1,2})?)',
    ]

    amounts = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches:
            cleaned = re.sub(r'[\s]', '', str(m)).replace(',', '.')
            try:
                val = float(cleaned)
                if 100 <= val <= 10_000_000:
                    amounts.append(val)
            except ValueError:
                pass
    return list(set(amounts))


async def read_group_history(client, group_name):
    """Read full message history from a Telegram group."""
    target = None
    async for dialog in client.iter_dialogs():
        if group_name.lower() in (dialog.name or "").lower():
            target = dialog
            break

    if not target:
        print(f"Group '{group_name}' not found.")
        return [], []

    print(f"Reading messages from '{target.name}'...")
    messages = []
    expenses = []
    count = 0

    async for msg in client.iter_messages(target.id, limit=None):
        count += 1
        data = {
            "id": msg.id,
            "date": msg.date.isoformat() if msg.date else None,
            "sender": None,
            "text": msg.text or "",
            "has_media": msg.media is not None,
        }

        if msg.sender:
            parts = []
            if hasattr(msg.sender, 'first_name') and msg.sender.first_name:
                parts.append(msg.sender.first_name)
            if hasattr(msg.sender, 'last_name') and msg.sender.last_name:
                parts.append(msg.sender.last_name)
            data["sender"] = " ".join(parts) if parts else str(msg.sender.id)

        messages.append(data)

        amounts = extract_amounts(msg.text)
        if amounts:
            expenses.append({
                "id": msg.id,
                "date": data["date"],
                "sender": data["sender"],
                "amounts": amounts,
                "text": (msg.text or "")[:500],
            })

        if count % 100 == 0:
            print(f"  Read {count} messages...")

    print(f"Total: {count} messages, {len(expenses)} expense records found.")
    return messages, expenses


async def main():
    if len(sys.argv) < 4:
        print("Usage: python bot.py <api_id> <api_hash> <group_name>")
        print("Or set env vars: TG_API_ID, TG_API_HASH")
        sys.exit(1)

    api_id = int(sys.argv[1])
    api_hash = sys.argv[2]
    group_name = sys.argv[3]

    client = TelegramClient(SESSION_FILE, api_id, api_hash)
    await client.start()

    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (@{me.username or 'N/A'})")

    messages, expenses = await read_group_history(client, group_name)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(os.path.join(OUTPUT_DIR, "messages.json"), "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    with open(os.path.join(OUTPUT_DIR, "expenses.json"), "w", encoding="utf-8") as f:
        json.dump(expenses, f, ensure_ascii=False, indent=2)

    if expenses:
        total = sum(a for e in expenses for a in e.get("amounts", []))
        print(f"\nTotal expenses found: {total:,.2f}")

    await client.disconnect()
    print("Done.")


if __name__ == "__main__":
    asyncio.run(main())
