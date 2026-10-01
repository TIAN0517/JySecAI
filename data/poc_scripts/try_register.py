#!/usr/bin/env python3
"""Try to register accounts via cmd=1080 with various parameters."""
import requests, urllib3, json
urllib3.disable_warnings()

url = "https://apib63.bf1788.com/boxApi.php"
base = {"vendorId": "test", "signature": "test", "site": "bfc", "lang": "tw"}

# Try different registration parameter combinations
attempts = [
    {"cmd": "1080", "wechatId": "testuser123", "wecha...[truncated]