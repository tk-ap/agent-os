#!/usr/bin/env python3
"""Capture the monitor group chat_id from a forwarded message in the private chat.

A forwarded message carries forward_origin/forward_from_chat with the source
chat id, which works even when the bot cannot read the group directly (privacy
mode) or when the "chat" is actually a channel.
"""
import json
import os
import sys
import time
import urllib.request

CONFIG = os.path.expanduser("~/.hermes/agent-os-telegram.json")


def call(tok, path):
    r = json.load(urllib.request.urlopen(f"https://api.telegram.org/bot{tok}/{path}", timeout=10))
    return r.get("result", [])


def chat_id_of(update):
    msg = update.get("message") or {}
    # Direct group message.
    if msg.get("chat", {}).get("type") in ("group", "supergroup"):
        return msg["chat"]["id"], msg["chat"].get("title", "untitled")
    # Forwarded from a group/channel.
    origin = msg.get("forward_origin") or {}
    if origin.get("type") in ("channel", "chat"):
        return origin.get("chat", {}).get("id"), origin.get("chat", {}).get("title", "untitled")
    fwd = msg.get("forward_from_chat") or {}
    if fwd.get("type") in ("channel", "group", "supergroup"):
        return fwd.get("id"), fwd.get("title", "untitled")
    return None, None


def main():
    config = json.load(open(CONFIG))
    tok = config["token"]
    private_id = config["chat_id"]
    deadline = time.monotonic() + 120
    offset = 0
    while time.monotonic() < deadline:
        updates = call(tok, "getUpdates?offset=%d&timeout=0&limit=100" % offset)
        for u in updates:
            offset = u["update_id"] + 1
            chat_id, title = chat_id_of(u)
            if chat_id and chat_id != private_id:
                config["monitor_chat_id"] = chat_id
                with open(CONFIG, "w") as fh:
                    json.dump(config, fh, indent=2)
                print(f"CAPTURED {title} {chat_id}")
                return
        time.sleep(1)
    print("NOTHING_CAPTURED")


if __name__ == "__main__":
    sys.exit(main())
