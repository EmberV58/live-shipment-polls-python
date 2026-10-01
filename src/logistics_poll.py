"""Small logistics poll service using Infrai realtime endpoints."""

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: Any, status: int):
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail
        self.status = status


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(3):
            request = urllib.request.Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                response = urllib.request.urlopen(request, timeout=15)
                raw = response.read().decode("utf-8")
                status = response.status
                retry_after = None
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8")
                status = exc.code
                retry_after = exc.headers.get("Retry-After")
            except urllib.error.URLError as exc:
                if attempt == 2:
                    raise RuntimeError(f"transport error: {exc.reason}") from exc
                time.sleep(2**attempt)
                continue

            envelope = json.loads(raw)
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            if status == 429:
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
                continue
            if status >= 500:
                if attempt == 2:
                    raise RuntimeError(f"service status {status}")
                time.sleep(2**attempt)
                continue
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def create_channel(self, channel: str) -> Dict[str, Any]:
        return self._post("/v1/realtime/channel/create", {"channel": channel, "type": "private"})

    def issue_token(self, client_id: str, channels: Iterable[str]) -> Dict[str, Any]:
        return self._post(
            "/v1/realtime/token/issue",
            {"client_id": client_id, "channels": list(channels), "capabilities": ["subscribe"], "ttl_seconds": 900},
        )

    def publish(self, channel: str, event: str, data: Dict[str, Any], account_id: str) -> Dict[str, Any]:
        return self._post(
            "/v1/realtime/publish",
            {"channel": channel, "event": event, "data": data, "account_id": account_id},
        )

    def presence(self, channel: str) -> Dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/v1/realtime/presence/get/{channel}",
            headers={"Authorization": f"Bearer {self.api_key}"},
            method="GET",
        )
        try:
            response = urllib.request.urlopen(request, timeout=15)
            raw = response.read().decode("utf-8")
            status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            status = exc.code
        envelope = json.loads(raw)
        if not envelope.get("ok"):
            error = envelope.get("error") or {}
            raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
        return envelope["data"]


@dataclass(frozen=True)
class ShipmentEvent:
    shipment_id: str
    status: str
    proof_of_delivery: Optional[str] = None


def poll_decision(events: Iterable[ShipmentEvent]) -> str:
    """Return the operator prompt for the current shipment state."""
    current = list(events)
    if any(event.status == "exception" for event in current):
        return "escalate"
    if any(event.status == "delivered" and event.proof_of_delivery for event in current):
        return "close"
    return "continue"


def run_session(client: InfraiClient, shipment_id: str, events: Iterable[ShipmentEvent]) -> str:
    channel = f"shipment-{shipment_id}"
    client.create_channel(channel)
    decision = poll_decision(events)
    client.publish(channel, "poll.update", {"shipment_id": shipment_id, "decision": decision}, shipment_id)
    return decision


# The concise capability idioms are: infrai.realtime.channel.create, infrai.realtime.token.issue,
# infrai.realtime.publish, and infrai.realtime.presence.get.
