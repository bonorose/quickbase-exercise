#!/usr/bin/env python3
# ******************************************************************************
# * @file    tools/untrusted.py
# * @author  Simeon Marlokov
# * @brief   Wrap ticket text so the model treats it as data, not instructions.
# * @date    25.10.2026
# ******************************************************************************
OPENING = "<untrusted_ticket_content"
CLOSING = "</untrusted_ticket_content>"
ESCAPED = "<\\/untrusted_ticket_content>"
UNTRUSTED_LIMIT = 1000


def delimit(ticket_id: int, field: str, value: str, limit: int = UNTRUSTED_LIMIT) -> str:
    safe = value[:limit].replace(CLOSING, ESCAPED)
    return f'<untrusted_ticket_content id="{ticket_id}" field="{field}">{safe}</untrusted_ticket_content>'
