from logistics_poll import InfraiClient, ShipmentEvent, run_session


def main() -> None:
    events = [ShipmentEvent("SHP-204", "delivered", proof_of_delivery="pod-204.pdf")]
    decision = run_session(InfraiClient(), "SHP-204", events)
    print({"shipment_id": "SHP-204", "decision": decision})


if __name__ == "__main__":
    main()
