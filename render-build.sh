#!/usr/bin/env bash
# ১. লাইব্রেরি ইন্সটল করা
pip install -r requirements.txt

# ২. Playwright এবং এর ব্রাউজার সঠিকভাবে ইন্সটল করা
python -m playwright install chromium
