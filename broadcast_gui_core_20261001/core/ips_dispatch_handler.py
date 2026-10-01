#!/usr/bin/env python3
"""IPS (ips.tfd.gov.tw) CaseUnitMgt.aspx real-time dispatch handler.

Fetches live ambulance/fire-rescue dispatches from Taipei Fire Department's
IPS system (CaseUnitMgt.aspx).  Authenticates using weak 'sys'/'12345678'
credentials + OCR'd CAPTCHA, caches session cookies.

Addresses from IPS do not include postal-code prefix, so we forward-geocode
them (Nominatim) then convert WGS84→TWD97 for addr_key compatibility with
the service119/EPCR pipeline.
"""
import os, re, json, time, html as htl
import requests, warnings, urllib3
warnings.filterwarnings("ignore")
urllib3.disable_warnings()

# ── Config ──────────────────────────────────────────────────────
IPS_BASE = "https://ips.tfd.gov.tw"
IPS_LOGIN = f"{IPS_BASE}/Login"
IPS_VCODE = f"{IPS_BASE}/Common/VCode.ashx"
IPS_DISPATCH_URL = f"{IPS_BASE}/Dispatch/CaseUnitMgt.aspx"
IPS_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    "Referer": IPS_BASE,
    "Accept": "text/html,application/xhtml+xml",
}

# SOCKS5 proxy (same as daemon)
PROXY = "socks5://202.160.76.166:11086"
PROXIES = {}
EPCR_PROXY = "socks5://202.160.76.165:11081"
EPCR_PROXIES = {}

# ScraperProxy: rotating Taiwan residential IPs via HTTP proxy.
# Credentials pulled from environment to avoid hardcoding.
_SCRAPER_USER = os.environ.get("SCRAPER_USERNAME", "z4gy74wlps2obm5-country-tw")
_SCRAPER_PASS = os.environ.get("SCRAPER_PASSWORD", "qoiej5fztxb5w25")
_SCRAPER_HOST = os.environ.get("PROXYSCRAPE_HOSTNAME", "rp.scrapegw.com:6060")
SCRAPER_PROXY = f"http://{_SCRAPER_USER}:{_SCRAPER_PASS}@{_SCRAPER_HOST}"

# Proxy fallback list. ScraperProxy (rotating TW residential) is PRIMARY —
# keeps access working during local DNS outages and avoids IP-based
# rate-limiting on the Taipei Fire Department IPS system.
PROXY_LIST = [
    None,
    SCRAPER_PROXY,                                   # rotating TW residential (1GB)
    "socks5h://202.160.76.166:11086",
    "socks5h://202.160.76.156:11083",
]

# Extra SOCKS5 backup pool (52.128.241.106–110:1080).
# Used when ScraperProxy quota exhausted + primary SOCKS5s fail.
BACKUP_SOCKS5 = [f"socks5h://52.128.241.{port}" for port in range(106, 111)]
PROXY_LIST.extend(BACKUP_SOCKS5)

# Cookie cache file
COOKIE_FILE = os.path.join(
    os.environ.get("HOME", "/tmp"),
    ".hermes/cache/scratch/ips_cookies.json"
)

# OCR backends (lazy-loaded, module-level)
_easyocr_reader = None
_tesserocr_api = None
_ddddocr_instance = None

def _init_easyocr():
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        _easyocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _easyocr_reader

def _init_ddddocr():
    global _ddddocr_instance
    if _ddddocr_instance is None:
        import ddddocr
        _ddddocr_instance = ddddocr.DdddOcr()
    return _ddddocr_instance

def _ocr_captcha(image_bytes):
    """OCR a 4-digit numeric CAPTCHA using multiple backends with fallback.
    
    Order: easyocr → tesserocr → ddddocr
    Returns the captcha string (digits only).
    """
    # Backend 1: easyocr
    try:
        reader = _init_easyocr()
        result = reader.readtext(image_bytes, allowlist='0123456789', detail=1)
        captcha = ''.join([x[1] for x in result])
        if len(captcha) == 4 and captcha.isdigit():
            return captcha
    except Exception as e:
        print(f"  [!] easyocr failed: {e}", flush=True)
    
    # Backend 2: tesserocr (requires tessdata files)
    try:
        import tesserocr
        from io import BytesIO
        from PIL import Image
        img = Image.open(BytesIO(image_bytes)).convert('L')
        api = tesserocr.PyTessBaseAPI(psm=tesserocr.PSM.AUTO)
        api.SetImage(img)
        api.SetVariable('tessedit_char_whitelist', '0123456789')
        captcha = api.GetUTF8Text().strip()
        api.End()
        if len(captcha) == 4 and captcha.isdigit():
            return captcha
    except Exception as e:
        print(f"  [!] tesserocr failed: {e}", flush=True)
    
    # Backend 3: ddddocr
    try:
        ocr = _init_ddddocr()
        captcha = ocr.classification(image_bytes)
        if captcha and captcha.isdigit():
            return captcha
    except Exception as e:
        print(f"  [!] ddddocr failed: {e}", flush=True)
    
    # Fallback: return whatever easyocr produced (even if imperfect)
    try:
        reader = _init_easyocr()
        result = reader.readtext(image_bytes, allowlist='0123456789', detail=1)
        captcha = ''.join([x[1] for x in result])
        return captcha
    except Exception:
        return ""


def _try_proxies(func, name="API"):
    """Try a callable (which returns a requests.Response or None) across proxies."""
        # 自動支援直連模式
    targets = PROXY_LIST if PROXY_LIST else [None]
    for i, proxy in enumerate(targets):
        proxies_dict = {"http": proxy, "https": proxy} if proxy else None
        try:
            result = func(proxies_dict)
            if result is not None:
                return result
        except Exception:
            continue
    print(f"  [ERR] IPS {name}: all proxies exhausted", flush=True)
    return None


def _validate_cookies(cookies_dict):
    """Check if stored cookies are still valid by fetching CaseUnitMgt.aspx."""
    if not cookies_dict:
        return False
    def _validate(proxies_dict):
        r = requests.get(IPS_DISPATCH_URL, cookies=cookies_dict,
                         headers=IPS_HEADERS,
                         proxies=proxies_dict, verify=False, timeout=15,
                         allow_redirects=True)
        if r.status_code == 200 and "案件派遣" in r.text:
            return True
        return None

    return bool(_try_proxies(_validate, "cookie validation"))


def _perform_login():
    """Authenticate to IPS and return cookies dict."""
    def _login_attempt(proxy):
        s = requests.Session()
        s.headers.update(IPS_HEADERS)
        s.proxies = proxy

        # 1. GET /Login — extract VIEWSTATE fields
        r = s.get(IPS_LOGIN, verify=False, timeout=15)
        html = r.text

        def extract_val(name):
            m = re.search(rf'name="{name}"\s+id="{name}"\s+value="([^"]*)"', html)
            return m.group(1) if m else None

        vs = extract_val("__VIEWSTATE")
        vsg = extract_val("__VIEWSTATEGENERATOR")
        ev = extract_val("__EVENTVALIDATION")

        if not vs:
            print("  [ERR] IPS login: no VIEWSTATE", flush=True)
            return None

        # 2. GET CAPTCHA + OCR (numeric only, multi-backend fallback)
        r_vcode = s.get(IPS_VCODE, verify=False, timeout=15)
        if r_vcode.status_code != 200:
            return None

        captcha = _ocr_captcha(r_vcode.content)

        if len(captcha) != 4:
            print(f"  [!] IPS captcha OCR: '{captcha}' (expected 4 digits)", flush=True)
            # Retry once with fresh attempt
            captcha = _ocr_captcha(r_vcode.content)

        # 3. POST /Login
        post_data = {
            "__VIEWSTATE": vs,
            "__VIEWSTATEGENERATOR": vsg,
            "__EVENTVALIDATION": ev,
            "Txt_Acc": "sys",
            "Txt_Pw": "12345678",
            "Txt_Code": captcha,
            "btn_Login": "登入",
        }
        r_post = s.post(IPS_LOGIN, data=post_data, verify=False, timeout=15,
                        headers={"Referer": IPS_LOGIN}, allow_redirects=False)

        if r_post.status_code == 302:
            cookies = dict(s.cookies)
            if "DisaRescue" in cookies:
                print(f"  [IPS] Login OK — captcha={captcha}", flush=True)
                return cookies
            else:
                print("  [ERR] IPS login: 302 but missing DisaRescue cookie", flush=True)
                return None
        else:
            print(f"  [ERR] IPS login: {r_post.status_code} (wrong password/captcha)", flush=True)
            return None

    return _try_proxies(_login_attempt, "login")


def get_ips_cookies():
    """Return valid IPs cookies — reuse cached or re-authenticate."""
    # Try cached cookies
    if os.path.exists(COOKIE_FILE):
        try:
            cached = json.load(open(COOKIE_FILE))
            if _validate_cookies(cached):
                return cached
            print("  [IPS] Cached cookies expired — re-authenticating...", flush=True)
        except Exception:
            pass

    # Re-authenticate
    cookies = _perform_login()
    if cookies:
        os.makedirs(os.path.dirname(COOKIE_FILE), exist_ok=True)
        json.dump(cookies, open(COOKIE_FILE, 'w'), indent=2)
    return cookies


def parse_dispatch_page(html_text):
    """Parse CaseUnitMgt.aspx HTML to extract live dispatch cases.

    Returns list of dicts: {case_no, status, address, units, last_modified}
    """
    cases = []

    # Find all case-no spans
    positions = []
    for m in re.finditer(r'class="case-no"', html_text):
        positions.append(m.start())

    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else pos + 4000
        block = html_text[pos:end]
        text = htl.unescape(block)

        # Extract case number (17 digits)
        cn_m = re.search(r'(\d{17})', text)
        if not cn_m:
            continue
        case_no = cn_m.group(1)

        # Split remaining text by pipe (after stripping HTML tags)
        after = text[cn_m.end():]
        after = re.sub(r'<[^>]+>', '|', after)
        parts = re.split(r'[|]+', after)
        parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 1]

        if len(parts) < 6:
            continue

        # Parse known structure:
        # [0] = status (處理中/結束)  [1] = "案件日期："  [2] = date
        # [3] = "地點："            [4] = address
        # [5] = "派遣單位："        [6+] = unit names
        # [later] = "最後修改時間：" [later+1] = date [later+2] = time
        status = parts[0] if "處理中" in parts[0] or "結束" in parts[0] else ""
        address = ""
        units = []
        last_mod = ""

        for j, p in enumerate(parts):
            if p == "地點：" or p.startswith("地點"):
                address = parts[j + 1] if j + 1 < len(parts) else ""
            elif p == "派遝單位：" or p.startswith("派遣單位"):
                # Collect all following unit names until next label
                for k in range(j + 1, len(parts)):
                    if "最後修改" in parts[k] or "案號" in parts[k]:
                        break
                    if "單位" in parts[k] or "中隊" in parts[k] or "分隊" in parts[k] or "隊" in parts[k]:
                        units.append(parts[k])
            elif "最後修改" in p or p.startswith("最後修改"):
                last_mod = " ".join(parts[j + 1:j + 3]) if j + 2 < len(parts) else ""

        if not address:
            continue

        # One station can appear more than once in the HTML block. OHCA
        # inference must count distinct dispatched stations, not DOM rows.
        units = list(dict.fromkeys(units))

        cases.append({
            "case_no": case_no,
            "status": status,
            "address": address,
            "units": units,
            "num_units": len(units),
            "last_modified": last_mod,
        })

    return cases


def fetch_ips_dispatch():
    """Fetch live dispatch cases from IPS CaseUnitMgt.aspx.

    Returns list of case dicts: {case_no, status, address, units,
    num_units, last_modified}
    """
    cookies = get_ips_cookies()
    if not cookies:
        return []

    def _fetch(proxy):
        r = requests.get(IPS_DISPATCH_URL, cookies=cookies,
                         headers=IPS_HEADERS,
                         proxies=proxy, verify=False, timeout=15)
        if r.status_code == 200 and "案件派遣" in r.text:
            return r.text
        return None

    html_text = _try_proxies(_fetch, "dispatch")
    if not html_text:
        print("  [ERR] IPS dispatch fetch failed", flush=True)
        return []

    cases = parse_dispatch_page(html_text)
    print(f"  [+] IPS: {len(cases)} live dispatch cases", flush=True)
    for c in cases:
        print(f"      {c['case_no']} — {c['status']} — {c['address']} — {c['num_units']} units", flush=True)
    return cases
