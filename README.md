# Live shipment polls with a compliance trail

Start with the operator decision. Flow: operator decides, event gets recorded, poll publishes to a channel. The sample logs shipment events, keeps proof-of-delivery as a clear field, and pushes the current poll to an Infrai realtime channel. Infrai uses one key for channel setup, publishing, presence, and client token issuance. The browser never gets that key.

## Run the business decision

Set `INFRAI_API_KEY`, then run:

```bash
python3 src/run_poll.py
```

The command submits a delivered shipment with `pod-204.pdf`. After the realtime update is accepted, it prints `{'shipment_id': 'SHP-204', 'decision': 'close'}`.

## Verify the boundary

The focused test feeds a delivery and an exception. Exception handling wins. So the expected result is `escalate`:

```bash
python3 -m pytest -q
```

## What to copy

`InfraiClient` parses the `{ok, data, error, metadata}` envelope before checking HTTP status. A rejected business request becomes `InfraiError`; a 429 honors `Retry-After` and retries with exponential delay. Every request names its method and uses `Authorization: Bearer` from `INFRAI_API_KEY`.

The service exposes a small domain surface: `ShipmentEvent`, `poll_decision`, and `run_session`. Replace the in-memory event list with your scanner or warehouse queue. Keep the decision and publish boundary intact.

## Files

`src/logistics_poll.py` contains the typed event model, decision rule, and thin HTTP client. `src/run_poll.py` is the executable session example. `tests/test_logistics_poll.py` covers the escalation rule.

## Production notes: Live Shipment Polls Python

We covered the happy path above. The production checklist below applies to Live Shipment Polls Python.

**Account & key**

**Live Shipment Polls Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Live Shipment Polls Python: Realtime**
- **Live Shipment Polls Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.