#!/usr/bin/env python3
"""
CryptoJS-compatible AES-256-CBC encryption for bear.emic.gov.tw.

AV is a 32-byte UTF-8 string. CryptoJS handles 32-byte keys directly as AES-256 (no padding).
"""
import base64
import json
from datetime import datetime
import uuid

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# Captured constant from api-clean.js (32 UTF-8 bytes)
AV = b"ab@37Tc54&2!T9621u65vt126g87ckpG"

def ov(plaintext: str) -> str:
    """Encrypt plaintext with CryptoJS AES-256-CBC + base64."""
    key = AV   # 32 bytes — AES-256 directly
    iv = AV[:16]  # first 16 bytes used as IV
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ct = cipher.encrypt(pad(plaintext.encode("utf-8"), AES.block_size))
    return base64.b64encode(ct).decode("ascii")


def sv(ciphertext_b64: str) -> str:
    """Decrypt base64 ciphertext (CryptoJS-compatible)."""
    key = AV
    iv = AV[:16]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    pt = unpad(cipher.decrypt(base64.b64decode(ciphertext_b64)), AES.block_size)
    return pt.decode("utf-8")


def make_sdata(payload: dict, times: str = None) -> str:
    """Build sDATA matching axios interceptor:
        {times, rand: crypto.randomUUID(), ...payload}
        JSON.stringify → ov() → base64
    """
    if times is None:
        times = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = {"times": times, "rand": str(uuid.uuid4()), **payload}
    return ov(json.dumps(body, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    # Sanity self-test
    msg = "hello world 2026"
    enc = ov(msg)
    dec = sv(enc)
    print(f"plaintext: {msg!r}")
    print(f"encrypted: {enc}")
    print(f"decrypted: {dec!r}")
    assert dec == msg, "roundtrip failed"

    # Build a sample sDATA
    sample = make_sdata({"ACTION": "probe"})
    print(f"sample sDATA: {sample}")
