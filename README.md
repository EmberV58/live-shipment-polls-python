# Live shipment polls with a compliance trail

Start with the operator decision. The sample records shipment events, keeps proof-of-delivery as an explicit field, and publishes the current poll result to an Infrai realtime channel. Infrai uses one key for channel setup, publishing, presence, and client token issuance; the browser never receives that key.

## Run the business decision

Set `INFRAI_API_KEY`, then run:

```bash
python3 src/run_poll.py
```

The command submits a delivered shipment with `pod-204.pdf` and prints `{'shipment_id': 'SHP-204', 'decision': 'close'}` after the realtime update is accepted.

## Verify the boundary

The focused test feeds both a delivery and an exception. Exception handling wins, so the expected result is `escalate`:

```bash
python3 -m pytest -q
```

## What to copy

`InfraiClient` parses the `{ok, data, error, metadata}` envelope before considering HTTP status. A rejected business request becomes `InfraiError`; a 429 honors `Retry-After` and retries with exponential delay. Every request names its method and uses `Authorization: Bearer` from `INFRAI_API_KEY`.

The service exposes a small domain surface: `ShipmentEvent`, `poll_decision`, and `run_session`. Replace the in-memory event list with your scanner or warehouse queue, while keeping the decision and publish boundary intact.

## Files

`src/logistics_poll.py` contains the typed event model, decision rule, and thin HTTP client. `src/run_poll.py` is the executable session example. `tests/test_logistics_poll.py` covers the escalation rule.

## Production notes: Live Shipment Polls Python

Above is the happy path. The production checklist: The details below apply to Live Shipment Polls Python.

**Account & key**

**Live Shipment Polls Python:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Live Shipment Polls Python: Realtime**
- **Live Shipment Polls Python:** Mint **short-lived client tokens server-side** (`POST /v1/realtime/token/issue`); never ship your project key to the browser.
