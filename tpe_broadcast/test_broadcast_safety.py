import unittest
from unittest.mock import patch

import broadcast_daemon as daemon


def incident(address="臺北市中正區測試路100號", **changes):
    case = {
        "source": "ips",
        "caseStatus": "處理中",
        "csPlace": address,
        "inTime": "2026-10-01 01:02:03",
        "csKindName": "救護",
        "dispatch_units": ["第一分隊"],
        "numberOfAmbulance": 1,
        "ips_case_no": "I-1",
    }
    case.update(changes)
    return case


class BroadcastSafetyTests(unittest.TestCase):
    def test_normal_message_supports_verified_original_without_coordinates(self):
        case = incident()
        captured = {}

        def capture(message, *_args, **_kwargs):
            captured["message"] = message
            return True

        with patch.object(daemon, "_broadcast_telegram_message", side_effect=capture):
            self.assertTrue(daemon.process_case(case, "01"))
        self.assertIn("來源未提供", captured["message"])

    def test_ohca_message_hides_internal_reason(self):
        cases = [
            incident(dispatch_units=["第一分隊"], ips_case_no="I-1"),
            incident(dispatch_units=["第二分隊"], ips_case_no="I-2"),
        ]
        captured = {}

        def capture(message, *_args, **_kwargs):
            captured["message"] = message
            return True

        with patch.object(daemon, "_broadcast_telegram_message", side_effect=capture):
            self.assertTrue(daemon.push_ohca_alert("01", cases, num_amb=2))
        self.assertIn("疑似 OHCA", captured["message"])
        self.assertNotIn("系統判讀", captured["message"])
        self.assertNotIn("判定依據", captured["message"])
        self.assertNotIn("同一報案地址", captured["message"])

    def test_institution_never_reaches_sender(self):
        with patch.object(daemon, "_broadcast_telegram_message") as sender:
            self.assertFalse(daemon.process_case(
                incident("臺北市中正區測試醫院100號"), "01"
            ))
        sender.assert_not_called()

    def test_non_taipei_or_cityless_address_never_reaches_sender(self):
        with patch.object(daemon, "_broadcast_telegram_message") as sender:
            self.assertFalse(daemon.process_case(
                incident("基隆市信義區測試路100號"), "01"
            ))
            self.assertFalse(daemon.process_case(
                incident("大安區測試路100號", ips_case_no="I-2"), "01"
            ))
        sender.assert_not_called()

    def test_ips_conversion_rejects_non_taipei_before_geocoding(self):
        raw = {
            "case_no": "I-OUTSIDE",
            "address": "基隆市信義區測試路100號",
            "status": "處理中",
            "units": ["第一分隊"],
            "num_units": 1,
            "last_modified": "2026-10-01 01:02:03",
        }
        with patch.object(daemon, "forward_geocode") as geocode:
            self.assertIsNone(daemon.ips_dispatch_to_case(raw, "01"))
        geocode.assert_not_called()

    def test_nearby_different_doorplates_are_not_merged(self):
        cases = [
            incident("臺北市中正區測試路100號", csX=302000, csY=2770000),
            incident("臺北市中正區測試路102號", csX=302001, csY=2770001,
                     ips_case_no="I-2", dispatch_units=["第二分隊"]),
        ]
        self.assertEqual(len(daemon._merge_nearby_ips_cases(cases)), 2)


if __name__ == "__main__":
    unittest.main()
