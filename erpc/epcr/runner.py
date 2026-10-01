"""主循環：EPCR GET /DispatchRecords StatusId 5/6；沒 JWT 才走 E1。不聽 socket。"""
from __future__ import annotations

import logging
import time

from .config import CFG
from .dest import targets
from .e1 import E1Feed
from .emic import EmicFeed
from .feed import EpcrFeed
from .tokens import TokenManager

log = logging.getLogger("epcr")


def run_forever() -> None:
    tokens = TokenManager()
    epcr = EpcrFeed(tokens)
    e1 = E1Feed(epcr.seen)
    emic = EmicFeed(epcr.seen)
    dests = ",".join(str(t.get("tenant")) for t in targets())
    log.info(
        "runner start poll=%ss dests=%s ntpc_only=%s dry_run=%s "
        "e1_backup=%s emic_backup=%s token_file=%s refresh_before=%ss",
        CFG.poll_sec,
        dests,
        CFG.ntpc_only,
        CFG.dry_run,
        CFG.e1_backup or CFG.e1_enabled,
        CFG.emic_backup,
        CFG.token_path,
        CFG.refresh_before_sec,
    )
    mode = ""
    while True:
        started = time.monotonic()
        try:
            if tokens.ensure(allow_login=False):
                if mode != "epcr":
                    log.info(
                        "primary=EPCR GET /DispatchRecords StatusId=%s remaining=%.0fs",
                        ",".join(str(x) for x in CFG.go_status_ids),
                        tokens.remaining(),
                    )
                    mode = "epcr"
                epcr.tick()
            else:
                epcr.last_ok = False
                if mode != "e1":
                    log.info(
                        "no jwt — wait %s ; backup=E1 source=E1 EMIC=%s",
                        CFG.token_path,
                        "on" if CFG.emic_backup else "off",
                    )
                    mode = "e1"
            if not epcr.last_ok:
                if CFG.e1_backup or CFG.e1_enabled:
                    e1.tick()
                if CFG.emic_backup:
                    emic.tick()
        except KeyboardInterrupt:
            raise
        except Exception:
            log.exception("runner tick")
            epcr.last_ok = False
        time.sleep(max(1.0, CFG.poll_sec - (time.monotonic() - started)))
