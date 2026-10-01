"""驗證碼 OCR。優先 ddddocr（扭曲字母），其次 Tesseract。"""
from __future__ import annotations

import logging
import re
from typing import Callable

log = logging.getLogger("epcr")

_ocr: Callable[[bytes], str] | None = None
_kind = ""


def _clean(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text or "")


def _load() -> None:
    global _ocr, _kind
    if _ocr is not None:
        return
    try:
        import ddddocr

        engine = ddddocr.DdddOcr(show_ad=False)

        def _dddd(data: bytes) -> str:
            return _clean(engine.classification(data))

        _ocr = _dddd
        _kind = "ddddocr"
        log.info("captcha ocr=ddddocr")
        return
    except Exception as exc:
        log.warning("ddddocr unavailable: %s", exc)
    try:
        import pytesseract
        from PIL import Image
        import io

        def _tess(data: bytes) -> str:
            img = Image.open(io.BytesIO(data)).convert("L")
            img = img.point(lambda x: 0 if x < 160 else 255)
            text = pytesseract.image_to_string(
                img,
                config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789",
            )
            return _clean(text)

        _ocr = _tess
        _kind = "tesseract"
        log.info("captcha ocr=tesseract")
        return
    except Exception as exc:
        log.warning("tesseract unavailable: %s", exc)
    _ocr = lambda _data: ""
    _kind = "none"
    log.error("no captcha OCR engine")


def solve(image: bytes) -> str:
    _load()
    assert _ocr is not None
    try:
        text = _ocr(image)
    except Exception as exc:
        log.warning("ocr fail: %s", exc)
        return ""
    log.info("ocr kind=%s text=%s", _kind, text)
    return text


def engine_name() -> str:
    _load()
    return _kind
