from datetime import datetime, timezone


def create_audit_event(event_type, message, details=None):
    """Create a structured audit event."""

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "message": message,
        "details": details or {}
    }


def add_audit_event(audit_log, event_type, message, details=None):
    """Add a new event to an existing audit log."""

    event = create_audit_event(
        event_type=event_type,
        message=message,
        details=details
    )

    audit_log.append(event)

    return event


if __name__ == "__main__":

    audit_log = []

    add_audit_event(
        audit_log,
        "PRODUCT_SELECTED",
        "Midnight Abaya selected as the best eligible product.",
        {
            "product": "Midnight Abaya",
            "price": 3599
        }
    )

    add_audit_event(
        audit_log,
        "POLICY_CHECK",
        "Purchase requires human approval.",
        {
            "decision": "REQUIRE_APPROVAL",
            "autonomous_limit": 1000
        }
    )

    add_audit_event(
        audit_log,
        "HUMAN_APPROVAL",
        "Transaction approved by human.",
        {
            "approved_by": "demo_user"
        }
    )

    print("\n--- AegisCart Audit Trail ---")

    for event in audit_log:
        print(f"\n[{event['event_type']}]")
        print(event["message"])
        print(f"Time: {event['timestamp']}")
        print(f"Details: {event['details']}")