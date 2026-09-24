# XSS rich v2 production candidate — Phase 1A.1

Baseline: bf7eaa8bace8b8a24c1a05a8c83754a4e7f5d2c9 (also the recorded Phase 1A baseline).
Prior patch SHA-256: 73bf10367082f55005b293dc8aca4a4a4ed7fc635237618e30ea5035b47a62ba.

Canonical schema retains rich TEXT/UUID IDs and every legacy evidence field.
Existing rows/scripts are never rewritten by the additive migration. A NULL or
empty per-payload token retains legacy global-token compatibility. New payloads
use random per-payload tokens. Management access is permission-scoped.

The simplified INTEGER implementation and DNS callback implementation are
replaced by the rich HTTP callback contract. The obsolete dns_exfil_domain
configuration field is removed. Old YAML/request keys cannot activate DNS
behavior; regression tests verify HTTP-only generated callbacks. No DNS schema
column is created. Existing legacy scripts remain immutable.

Verification uses private network namespaces and synthetic localhost fixtures
only. Production configuration, production databases, production binaries and
service processes are outside the change scope. The guarded --xss-shadow-db
entrypoint permits migration only on a marked shadow.db copy; optional shadow
startup runs an ephemeral loopback health endpoint, not normal Core startup.

The full hash manifest and fresh verification records are maintained outside this
commit in D:/AI/Reports/xss-schema-v2-phase1a1-20260924. Phase 1B must use the exact
frozen binary SHA-256. Any source change requires renewed acceptance. No deployment
or merge is authorized by this candidate.
