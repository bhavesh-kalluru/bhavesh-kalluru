#!/usr/bin/env python3
import json, re, datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
QUOTES = ROOT / "data" / "quotes.json"

START = "<!-- DAILY:QUOTE -->"
END = "<!-- END:QUOTE -->"

def pick_item(items):
    # deterministic rotation by date (no repeats until cycle)
    today = dt.date.today().toordinal()
    return items[today % len(items)]

def render_quote(q):
    text = q.get("text", "").strip()
    author = q.get("author", "").strip()
    if author:
        return f'> “{text}” — {author}'
    return f'> “{text}”'

def replace_block(content, start_marker, end_marker, new_text):
    pattern = re.compile(
        rf"{re.escape(start_marker)}.*?{re.escape(end_marker)}",
        flags=re.DOTALL
    )
    replacement = f"{start_marker}\n{new_text}\n{end_marker}"
    if pattern.search(content):
        return pattern.sub(replacement, content)
    # If markers missing, append at end under a header fallback
    return content.rstrip() + f"\n\n### 🎯 Favorite Quote\n\n{replacement}\n"

def main():
    if not README.exists():
        raise SystemExit("README.md not found at repo root")

    try:
        quotes = json.loads(QUOTES.read_text(encoding="utf-8"))
        if not quotes:
            raise ValueError("quotes.json is empty")
    except Exception:
        # reliable fallback
        quotes = [{"text": "Make it work, make it right, make it fast.", "author": "Kent Beck"}]

    chosen = pick_item(quotes)
    new_quote_md = render_quote(chosen)

    original = README.read_text(encoding="utf-8")
    updated = replace_block(original, START, END, new_quote_md)

    if updated != original:
        README.write_text(updated, encoding="utf-8")
        print("README updated with new quote.")
    else:
        print("No change required.")

if __name__ == "__main__":
    main()
