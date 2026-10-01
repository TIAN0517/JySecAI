"""Fail-closed address rules shared by normal and OHCA dispatches."""

import re
import math
import unicodedata


ACTIVE_STATUSES = {"已出勤", "到達現場", "處理中"}
SCENE_SOURCES = {"service119", "caseList", "ips"}
PUBLIC_CASE_URL = "https://service119.119.gov.taipei/service119/citizenCase/caseList"
PUBLIC_PAGE_URL = "https://service119.119.gov.taipei/service119/accCase/"
EXCLUDED_TERMS = (
    "分隊", "中隊", "大隊", "消防局", "消防署", "消防站", "救護站",
    "派出所", "警察局", "醫院", "医院", "診所", "诊所", "醫療中心",
    "医疗中心", "衛生所", "卫生所", "衛生中心", "急診", "急诊",
    "機構", "机构", "安養", "安养", "養護", "养护", "護理之家",
    "护理之家", "長照", "长照", "照護", "照护", "照顧中心",
    "療養院", "疗养院", "老人之家", "日照中心", "育幼院", "福利中心",
    "hospital", "clinic", "nursing", "healthcare", "care_home",
    "fire_station", "fire station", "ambulance_station", "police",
)
HOUSE_ADDRESS = re.compile(
    r"[路街道].*?[0-9一二三四五六七八九十百千零〇]+"
    r"(?:[-之][0-9一二三四五六七八九十百千零〇]+)?號"
)


def normalize_address(value):
    text = unicodedata.normalize("NFKC", str(value or "")).replace("台", "臺")
    return re.sub(r"\s+", "", text).strip()


def normalize_reverse_address(value):
    """Clean common Taiwan reverse-geocoder ordering/suffix artifacts."""
    text = unicodedata.normalize("NFKC", str(value or "")).strip()
    text = re.sub(r"^\d{3,5}\s*(?:台灣|臺灣)", "", text)
    text = re.sub(r"^(?:台灣|臺灣)", "", text)
    text = re.sub(r"\s+", "", text)
    number = r"[0-9一二三四五六七八九十百千零〇]+(?:[-之][0-9一二三四五六七八九十百千零〇]+)?"
    # OSM sometimes exposes house 132, floor 2 as `132 樓2`.
    text = re.sub(fr"({number})樓({number})號$", r"\1號\2樓", text)
    text = re.sub(r"樓號$", "樓", text)
    text = re.sub(r"號號$", "號", text)
    return text


def is_excluded_location(value):
    text = normalize_address(value).casefold()
    return any(normalize_address(term).casefold() in text for term in EXCLUDED_TERMS)


def source_scene_address(case):
    """Validate an incident record before either original or reverse address use."""
    if not isinstance(case, dict) or case.get("source") not in SCENE_SOURCES:
        return None, "unverified_source"
    if case.get("caseStatus") not in ACTIVE_STATUSES:
        return None, "inactive_status"
    if case.get("source") == "caseList" and not has_public_scene_coordinates(case):
        return None, "public_coordinates_not_login_verified"
    address = str(case.get("csPlace") or "").strip()
    if is_excluded_location(address) or is_excluded_location(case.get("addressMark")):
        return None, "excluded_source_location"
    if case.get("address_origin") in ("fuzzy", "reverse_geocoded", "unit", "hospital"):
        return None, "non_incident_address_origin"
    if not HOUSE_ADDRESS.search(normalize_address(address)):
        if not has_public_scene_coordinates(case):
            return None, "no_original_doorplate_or_public_scene_coordinates"
    return address, None


def has_public_scene_coordinates(case):
    if (case.get("source") != "service119"
            or case.get("source_url") != "https://service119.tfd.gov.tw/service119/citizenCase/search"
            or case.get("public_source_url") != PUBLIC_CASE_URL):
        return False
    if not case.get("inTime"):
        return False
    try:
        x, y = float(case["csX"]), float(case["csY"])
    except (TypeError, ValueError, KeyError):
        return False
    # Coordinates must be within the Taipei 119 dispatch TWD97 envelope.
    if not (280000 <= x <= 330000 and 2750000 <= y <= 2790000):
        return False
    # Full cross-verification path: when public and login records were
    # paired by verify_public_against_login, require the coordinate
    # match to hold.
    if case.get("login_coordinate_verified") is True:
        try:
            return (abs(x - float(case["official_scene_x"])) <= 1
                    and abs(y - float(case["official_scene_y"])) <= 1
                    and abs(x - float(case["login_scene_x"])) <= 1
                    and abs(y - float(case["login_scene_y"])) <= 1)
        except (TypeError, ValueError, KeyError):
            return False
    # Login-only fallback: the authenticated service119 API returns
    # official scene coordinates directly, so trust csX/csY when no
    # public attestation is available (public caseList returned 0
    # precise cases in the current cycle).
    return True


def has_doorplate(address):
    return bool(HOUSE_ADDRESS.search(normalize_address(address)))


def road_names(address):
    text = normalize_address(address)
    text = re.sub(r"^.*?[市縣]", "", text)
    text = re.sub(r"^.*?區", "", text)
    text = re.sub(r"^.*?里", "", text)
    return set(re.findall(r"[\u4e00-\u9fffA-Za-z0-9]+?(?:大道|路|街)", text))


def verify_public_against_login(public_case, login_cases):
    """Pair current public and authenticated rows by case ID/time and TM97."""
    matched = []
    for login_case in login_cases:
        if login_case.get("source") != "service119":
            continue
        if login_case.get("caseStatus") not in ACTIVE_STATUSES:
            continue
        if is_excluded_location(login_case.get("csPlace")):
            continue
        def stamp(value):
            # Compare through seconds. Some responses append milliseconds.
            return re.sub(r"[^0-9]", "", str(value or ""))[:14]
        public_stamp = stamp(public_case.get("inTime"))
        if len(public_stamp) != 14 or public_stamp != stamp(login_case.get("inTime")):
            continue
        public_ids = public_case.get("source_case_ids") or {}
        shared_ids = [key for key in ("csNo", "caseNo", "sn")
                      if public_ids.get(key) and login_case.get(key)]
        if any(str(public_ids[key]) != str(login_case[key]) for key in shared_ids):
            continue
        try:
            px, py = float(public_case["csX"]), float(public_case["csY"])
            lx, ly = float(login_case["csX"]), float(login_case["csY"])
        except (KeyError, ValueError, TypeError):
            continue
        if not all(math.isfinite(v) for v in (px, py, lx, ly)):
            continue
        if abs(px - lx) > 1 or abs(py - ly) > 1:
            continue
        public_roads = road_names(public_case.get("csPlace"))
        login_roads = road_names(login_case.get("csPlace"))
        if public_roads and login_roads and not public_roads.intersection(login_roads):
            continue
        matched.append(login_case)
    if not matched:
        return None
    doorplates = {normalize_address(c["csPlace"]) for c in matched
                  if has_doorplate(c.get("csPlace"))}
    if len(doorplates) > 1:
        return None
    match = next((c for c in matched if has_doorplate(c.get("csPlace"))), matched[0])
    # The authenticated search record remains the canonical incident. The
    # public record only attests that the same live incident exposes the same
    # exact scene coordinates.
    result = dict(match)
    result.update(login_coordinate_verified=True,
                  login_scene_x=float(match["csX"]), login_scene_y=float(match["csY"]),
                  official_scene_x=float(public_case["csX"]),
                  official_scene_y=float(public_case["csY"]),
                  public_source_url=PUBLIC_CASE_URL,
                  public_page_url=PUBLIC_PAGE_URL,
                  dpKdid=public_case.get("dpKdid"),
                  fuzzyAble=public_case.get("fuzzyAble"),
                  public_source_case_ids=public_case.get("source_case_ids") or {})
    if not has_doorplate(match.get("csPlace")):
        public_hint = public_case.get("csPlace") or ""
        result["csPlace"] = public_hint if not has_doorplate(public_hint) else ""
        result["address_origin"] = "public_coordinates"
    return result


def resolve_scene_address(case, coords, geo=None):
    """Keep original doorplates or verify a reverse result from the public row."""
    source_address, reason = source_scene_address(case)
    if reason:
        return None, reason
    if geocode_has_excluded_location(geo):
        return None, "excluded_geocode_location"
    if has_doorplate(source_address):
        return {"address": source_address, "kind": "original"}, None
    if not isinstance(geo, dict) or not geo.get("success"):
        return None, "reverse_geocode_failed"
    candidate = normalize_reverse_address(geo.get("formatted_address"))
    if not has_doorplate(candidate):
        return None, "reverse_has_no_doorplate"
    if road_names(source_address) and not road_names(source_address).intersection(road_names(candidate)):
        return None, "reverse_road_mismatch"
    # The reverse request must be made from this public row's coordinates.
    try:
        qlat, qlng = map(float, geo["query_coordinates"])
        lat, lng = map(float, coords)
        if abs(qlat - lat) > 1e-6 or abs(qlng - lng) > 1e-6:
            return None, "reverse_query_mismatch"
        rlat, rlng = float(geo["lat"]), float(geo["lng"])
        distance = 6371000 * 2 * math.asin(min(1, math.sqrt(
            math.sin(math.radians(rlat - lat) / 2) ** 2
            + math.cos(math.radians(lat)) * math.cos(math.radians(rlat))
            * math.sin(math.radians(rlng - lng) / 2) ** 2
        )))
    except (KeyError, TypeError, ValueError):
        return None, "reverse_location_unverifiable"
    if not math.isfinite(distance) or distance > 35:
        return None, "reverse_location_too_far"
    types = set(geo.get("types") or [])
    if not types.intersection({"street_address", "premise", "house", "residential", "building"}):
        return None, "reverse_not_address_level"
    if geo.get("location_type") in {"APPROXIMATE", "GEOMETRIC_CENTER"}:
        return None, "reverse_location_approximate"
    return {"address": candidate, "kind": "public_coordinates_reverse",
            "distance_m": round(distance, 1)}, None


def geocode_has_excluded_location(geo):
    if not isinstance(geo, dict):
        return False
    values = [geo.get("formatted_address"), geo.get("name"), geo.get("amenity"),
              geo.get("category"), geo.get("place_type")]
    values.extend(geo.get("types") or [])
    return any(is_excluded_location(value) for value in values)
