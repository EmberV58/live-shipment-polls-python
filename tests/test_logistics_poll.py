from src.logistics_poll import ShipmentEvent, poll_decision


def test_exception_event_escalates_before_delivery_close() -> None:
    events = [
        ShipmentEvent("SHP-7", "delivered", proof_of_delivery="pod-7.pdf"),
        ShipmentEvent("SHP-7", "exception"),
    ]
    assert poll_decision(events) == "escalate"
