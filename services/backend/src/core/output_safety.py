#!/usr/bin/env python3
# ******************************************************************************
# * @file    output_safety.py
# * @author  Simeon Marlokov
# * @brief   Strip outbound links from assistant text so ticket contents cannot exfiltrate.
# * @date    26.10.2026
# ******************************************************************************
import re

_IMAGE = re.compile(r"!\[[^\]]*\]\(\s*https?://[^)\s]+\)", re.IGNORECASE)
_URL = re.compile(r"https?://\S+", re.IGNORECASE)


def scrub_assistant_text(text: str) -> str:
    cleaned = _IMAGE.sub("[image removed]", text)
    return _URL.sub("[link removed]", cleaned)
