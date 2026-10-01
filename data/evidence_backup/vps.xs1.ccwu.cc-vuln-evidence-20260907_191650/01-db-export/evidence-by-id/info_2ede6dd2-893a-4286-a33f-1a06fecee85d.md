# www.tzuchi.org.tw 泄露 Cloudflare Pages Analytics 令牌与 GTM 容器 ID

- ID: `2ede6dd2-893a-4286-a33f-1a06fecee85d`
- Severity: **info**
- Status: open
- Type: Sensitive Information Disclosure
- Target: `https://www.tzuchi.org.tw/`
- Conversation: `3b694297-0b84-41bc-a589-66652e232956`
- Created: 2026-09-02 20:07:40.070009572+08:00

## Description

https://www.tzuchi.org.tw/ homepage (166,596B) exposes a live Cloudflare Pages Analytics write key and a Google Tag Manager container ID. The analytics token appears in an inline Cloudflare Web Analytics snippet; GTM container loaded via scripts. These identifiers can be leveraged for analytics data manipulation / tag-based data collection, and confirm the deployment platform.

## Reproduction

1) GET https://www.tzuchi.org.tw/ 2) grep for 'cloudflare' analytics token and 'GTM-' container ID in the inline <script> blocks.

## Evidence

Inline script: cloudflare-insights init with token "89a101ba7676403580395a42d1075e85"; GTM container "GTM-KD3PM6KH" loaded on the public homepage. Confirmed via GET https://www.tzuchi.org.tw/ (HTTP/2 200, 166596 bytes).

## Impact

Low/Info. Exposed third-party tracking identifiers (Cloudflare Pages Analytics token, GTM ID) reveal deployment tooling and can be abused to submit crafted analytics events or correlate tracking. No direct data breach.

## Recommendation

Rotate the Cloudflare Pages Analytics write token and restrict GTM tag visibility; avoid embedding long-lived secrets/tokens in public static HTML.
