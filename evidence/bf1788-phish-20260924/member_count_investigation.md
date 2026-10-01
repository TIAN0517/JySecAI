=== bf1788 API Member Count Investigation ===
Date: 2026-09-24

Finding: NO endpoint returns platform-wide total member count.

What we know:
1. cmd=518 (game level config): Shows 5 VIP levels within game group BF001
   - Level A (default):     1,443 members
   - Level X (upper):         476 members
   - Level C (USDT):            8 members
   - Level A (withdrawal):      6 members
   - Level B (convenience):    13 members
   - Sum: 1,946 (BUT levels may overlap — NOT a unique total)

2. cmd=516 (agent line): Account ID = 1909
   - Suggests at least 1,909+ registered accounts exist
   - mline: "1909," (agent referral line)

3. cmd=302 (game catalog): 15,018 games, no member fields
4. cmd=300 (game halls): 247 halls, no member count fields
5. cmd=301 (game groups): 341 groups, no member count fields

6. Admin cmd scan (1001-2000, 10001-10020): No total member endpoint found
   Only hit: cmd=1002 returns "請輸入手機" (phone input required)

Conclusion: Platform uses per-group/per-level member counts.
Estimated total: 341 game groups × avg ~1,946 members = 660,000+ potential members
(But this is speculative — no verification endpoint exists)

Test account limitation: cffcna6qzp (id=1909) has zero financial activity,
so all payment/KYC fields are empty. Real victims would have full data.