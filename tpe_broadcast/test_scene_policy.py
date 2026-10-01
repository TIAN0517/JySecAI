import unittest

from scene_policy import (
    PUBLIC_CASE_URL,
    normalize_reverse_address,
    resolve_scene_address,
    source_scene_address,
    verify_public_against_login,
)


SEARCH_URL = "https://service119.tfd.gov.tw/service119/citizenCase/search"


def login_case(**changes):
    case = {
        "source": "service119",
        "source_url": SEARCH_URL,
        "inTime": "2026-10-01 01:02:03",
        "caseStatus": "到達現場",
        "csPlace": "臺北市中正區測試路100號",
        "csX": 302000.0,
        "csY": 2770000.0,
        "caseNo": "C-1",
    }
    case.update(changes)
    return case


def public_case(**changes):
    case = {
        "source": "caseList",
        "source_url": PUBLIC_CASE_URL,
        "inTime": "2026-10-01 01:02:03.000",
        "caseStatus": "到達現場",
        "csPlace": "臺北市中正區測試路",
        "csX": 302000.4,
        "csY": 2770000.4,
        "official_scene_x": 302000.4,
        "official_scene_y": 2770000.4,
        "dpKdid": "A",
        "fuzzyAble": "N",
        "source_case_ids": {"caseNo": "C-1"},
    }
    case.update(changes)
    return case


class CoordinateCorrelationTests(unittest.TestCase):
    def test_authenticated_case_is_canonical_after_match(self):
        result = verify_public_against_login(public_case(), [login_case()])
        self.assertIsNotNone(result)
        self.assertEqual(result["source"], "service119")
        self.assertEqual(result["csPlace"], "臺北市中正區測試路100號")
        self.assertTrue(result["login_coordinate_verified"])
        self.assertEqual(result["public_source_url"], PUBLIC_CASE_URL)

    def test_coordinate_only_login_case_can_be_enriched(self):
        result = verify_public_against_login(
            public_case(csPlace="臺北市中正區測試路"),
            [login_case(csPlace="")],
        )
        self.assertEqual(result["csPlace"], "臺北市中正區測試路")
        self.assertEqual(result["address_origin"], "public_coordinates")
        self.assertIsNone(source_scene_address(result)[1])

    def test_mismatched_time_id_or_coordinate_is_rejected(self):
        self.assertIsNone(verify_public_against_login(
            public_case(inTime="2026-10-01 01:02:04"), [login_case()]
        ))
        self.assertIsNone(verify_public_against_login(
            public_case(source_case_ids={"caseNo": "OTHER"}), [login_case()]
        ))
        self.assertIsNone(verify_public_against_login(
            public_case(csX=302010.0), [login_case()]
        ))

    def test_institution_source_is_rejected(self):
        result = verify_public_against_login(
            public_case(csPlace="臺北市立醫院"),
            [login_case(csPlace="臺北市立醫院")],
        )
        self.assertIsNone(result)


class AddressResolutionTests(unittest.TestCase):
    def test_reverse_address_floor_format_is_normalized(self):
        self.assertEqual(
            normalize_reverse_address("114 台灣臺北市內湖區測試路132 樓2號"),
            "臺北市內湖區測試路132號2樓",
        )
        self.assertEqual(
            normalize_reverse_address("臺北市內湖區測試路30號二樓號"),
            "臺北市內湖區測試路30號二樓",
        )

    def test_original_doorplate_is_never_replaced(self):
        case = login_case()
        geo = {
            "success": True,
            "formatted_address": "臺北市中正區附近路2號",
            "types": ["street_address"],
            "lat": 25.0,
            "lng": 121.0,
            "query_coordinates": [25.0, 121.0],
        }
        result, reason = resolve_scene_address(case, (25.0, 121.0), geo)
        self.assertIsNone(reason)
        self.assertEqual(result["address"], case["csPlace"])
        self.assertEqual(result["kind"], "original")

    def test_correlated_coordinate_can_fill_address(self):
        case = verify_public_against_login(
            public_case(), [login_case(csPlace="臺北市中正區測試路")]
        )
        geo = {
            "success": True,
            "formatted_address": "臺北市中正區測試路100號",
            "types": ["street_address"],
            "location_type": "ROOFTOP",
            "lat": 25.00005,
            "lng": 121.0,
            "query_coordinates": [25.0, 121.0],
        }
        result, reason = resolve_scene_address(case, (25.0, 121.0), geo)
        self.assertIsNone(reason)
        self.assertEqual(result["kind"], "public_coordinates_reverse")

    def test_far_or_institution_reverse_result_is_rejected(self):
        case = verify_public_against_login(
            public_case(), [login_case(csPlace="臺北市中正區測試路")]
        )
        far_geo = {
            "success": True,
            "formatted_address": "臺北市中正區測試路100號",
            "types": ["street_address"],
            "lat": 25.001,
            "lng": 121.0,
            "query_coordinates": [25.0, 121.0],
        }
        self.assertEqual(
            resolve_scene_address(case, (25.0, 121.0), far_geo)[1],
            "reverse_location_too_far",
        )
        hospital_geo = dict(far_geo, lat=25.0,
                            formatted_address="臺北市中正區測試醫院100號")
        self.assertEqual(
            resolve_scene_address(case, (25.0, 121.0), hospital_geo)[1],
            "excluded_geocode_location",
        )

    def test_uncorrelated_coordinate_is_rejected(self):
        case = login_case(csPlace="臺北市中正區測試路")
        self.assertEqual(
            source_scene_address(case)[1],
            "no_original_doorplate_or_public_scene_coordinates",
        )


if __name__ == "__main__":
    unittest.main()
