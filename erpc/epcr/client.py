"""帶 JWT 的 EPCR API。401 先 refresh 再重試。"""
from __future__ import annotations

import json
import logging
from typing import Any

from .config import CFG
from .http import as_list, curl, encode_jq
from .tokens import TokenManager

log = logging.getLogger("epcr")


class EpcrClient:
    def __init__(self, tokens: TokenManager | None = None) -> None:
        self.tokens = tokens or TokenManager()

    def _get(self, url: str, *, auth_needed: bool = True) -> tuple[int, Any]:
        tok = self.tokens.bearer() if auth_needed else ""
        result = curl(url, auth=auth_needed, token=tok, timeout=CFG.timeout, retries=1)
        if auth_needed and result.status == 401:
            if self.tokens.ensure(force=True):
                result = curl(
                    url, auth=True, token=self.tokens.bearer(), timeout=CFG.timeout, retries=0
                )
        if result.status != 200:
            return result.status, {"error": result.error or result.text()[:240]}
        try:
            return result.status, result.json()
        except json.JSONDecodeError:
            return result.status, result.text()

    def go_dispatches(self) -> tuple[int, list]:
        query = encode_jq({"StatusId": {"$in": list(CFG.go_status_ids)}})
        code, data = self._get(f"{CFG.base_4000}/DispatchRecords?{query}")
        return code, as_list(data) if code == 200 else []

    def case_main(self, case_no: str) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/CaseRecords/getCaseMain/{case_no}")

    def case_type_name(self, case_no: str) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/CaseRecords/CaseTypeNameByCaseNo/{case_no}")

    def case_description(self, record_uuid: str) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/CaseRecords/CaseDescriptionOf/{record_uuid}")

    def pcr_only(self, pcr_uuid: str) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/pcrOnly/{pcr_uuid}")

    def pcr_uuid_by_case_sn(self, case_sn: str) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/Pcrs/PcrUuidByCaseSN/{case_sn}")

    def dispatch_record(self, uuid: str) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/DispatchRecords/{uuid}")

    def list_branch_with_case(self) -> tuple[int, Any]:
        return self._get(f"{CFG.base_4000}/Branches/listBranchWithCaseRecordAndAmbulance")
