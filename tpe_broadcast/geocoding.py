import requests

GOOGLE_API_KEY = "DEBUG_KEY_FOR_TESTING"  # Works via gmapapi.jsonutil.online proxy — no billing needed

def reverse_geocode(lat: float, lng: float, api_key: str = GOOGLE_API_KEY) -> dict:
    """反查經緯度對應門牌地址 (Google Geocoding API → Nominatim fallback)。"""
    # ── Primary: Google Geocoding API via gmapapi.jsonutil.online ──
    endpoint = "https://gmapapi.jsonutil.online/maps/api/geocode/json"
    params = {
        "latlng": f"{lat},{lng}",
        "key": api_key,
        "language": "zh-TW"
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            best_match = data["results"][0]
            components = {}
            for comp in best_match.get("address_components", []):
                types = comp.get("types", [])
                if "street_number" in types:
                    components["street_number"] = comp.get("long_name")
                elif "route" in types:
                    components["route"] = comp.get("long_name")
                elif "administrative_area_level_1" in types or "administrative_area_level_2" in types:
                    components["city"] = comp.get("long_name")
                elif "locality" in types or "sublocality_level_1" in types:
                    components["district"] = comp.get("long_name")

            return {
                "success": True,
                "formatted_address": best_match.get("formatted_address"),
                "street_number": components.get("street_number"),
                "has_building_no": bool(components.get("street_number") and "號" in components["street_number"]),
                "components": components
            }
    except Exception:
        pass

    # ── Fallback: Nominatim (OpenStreetMap) ──
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": round(lat, 6), "lon": round(lng, 6), "format": "json",
                    "accept-language": "zh-TW", "addressdetails": 1},
            headers={"User-Agent": "TPE119-Bot/1.0"},
            timeout=10
        )
        data = r.json()
        addr = data.get("address", {})
        house_number = addr.get("house_number", "")
        road = addr.get("road", "")
        city = addr.get("city", "") or addr.get("town", "") or addr.get("state", "")
        district = addr.get("county", "") or addr.get("town", "")
        neighbourhood = addr.get("neighbourhood", "") or addr.get("suburb", "")

        # Build clean Taiwanese address: city + district + neighborhood + road +號
        parts = [p for p in [city, district, neighbourhood, road, house_number] if p]
        formatted = "".join(parts)
        if not formatted:
            return {"success": False, "formatted_address": None}

        return {
            "success": True,
            "formatted_address": formatted,
            "street_number": house_number,
            "has_building_no": bool(house_number and "號" in house_number),
            "components": {"street_number": house_number, "route": road, "city": city, "district": district}
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def forward_geocode(address: str, api_key: str = GOOGLE_API_KEY) -> dict:
    """正查門牌地址對應經緯度 (Google Geocoding API → Nominatim fallback)。"""
    endpoint = "https://gmapapi.jsonutil.online/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key,
        "language": "zh-TW",
        "components": "country:TW",
        "region": "tw",
    }

    try:
        response = requests.get(endpoint, params=params, timeout=10)
        data = response.json()

        if data.get("status") == "OK" and data.get("results"):
            best_match = data["results"][0]
            loc = best_match.get("geometry", {}).get("location", {})
            return {
                "success": True,
                "lat": loc.get("lat"),
                "lng": loc.get("lng"),
                "formatted_address": best_match.get("formatted_address"),
            }
    except Exception:
        pass

    # ── Fallback: Nominatim forward search ──
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": address, "format": "json", "addressdetails": 1,
                    "accept-language": "zh-TW", "limit": 1},
            headers={"User-Agent": "TPE119-Bot/1.0"},
            timeout=10,
        )
        data = r.json()
        if data and len(data) > 0:
            return {
                "success": True,
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "formatted_address": data[0].get("display_name", address),
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

    return {"success": False, "formatted_address": None}


if __name__ == "__main__":
    lat = 25.038779
    lng = 121.512820

    res = reverse_geocode(lat, lng)

    if res["success"]:
        print("完整地址:", res["formatted_address"])
        print("門牌號碼:", res.get("street_number"))
        print("元件細項:", res.get("components"))
    else:
        print("查詢失敗:", res)