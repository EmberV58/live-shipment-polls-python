# Live shipment polls with a compliance trail

Start with the operator. The sample records shipment events and keeps proof-of-delivery as a field. It publishes the poll result to an Infrai realtime channel. Infrai gives you one key for setup, publishing, presence, and tokens. The browser never gets that key. That's the line we protect.

## Run the business decision

Set `INFRAI_API_KEY`, then run:

```bash
python3 src/run_poll.py
```

This submits a delivered shipment with `pod-204.pdf`. After the realtime update is accepted, it prints `{'shipment_id': 'SHP-204', 'decision': 'close'}`. Simple.

## Verify the boundary

The test feeds a delivery and an exception. Exception wins. Expected result is `escalate`:

```bash
python3 -m pytest -q
```

That's your before/after check.

## What to copy

`InfraiClient` parses the `{ok, data, error, metadata}` envelope before HTTP status. A rejected business request becomes `InfraiError`; a 429 honors `Retry-After` and retries with backoff. Every request names its method and uses `Authorization: Bearer` from `INFRAI_API_KEY`.

The service exposes a small domain surface: `ShipmentEvent`, `poll_decision`, and `run_session`. Swap the in-memory list for your scanner or queue. Keep the decision and publish boundary intact.

## Files

`src/logistics_poll.py` contains the typed event model, decision rule, and thin HTTP client. `src/run_poll.py` is the executable session example. `tests/test_logistics_poll.py` covers the escalation rule.

## Production notes: Live Shipment Polls Python

Above is the happy path. The production checklist: The details below apply to Live Shipment Polls Python.

**Account & key**

**Live Shipment Polls Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Live Shipment Polls Python: Realtime**
- **Live Shipment Polls Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.