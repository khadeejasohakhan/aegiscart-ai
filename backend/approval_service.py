from audit_service import add_audit_event


def request_approval(transaction):
    """
    Check whether a transaction is eligible
    to enter the human approval process.
    """

    if transaction["status"] != "AWAITING_HUMAN_APPROVAL":
        return {
            "success": False,
            "status": transaction["status"],
            "message": "Transaction is not awaiting human approval."
        }

    return {
        "success": True,
        "status": "AWAITING_HUMAN_APPROVAL",
        "message": "Human approval is required before payment."
    }


def approve_transaction(transaction, approved_by):
    """
    Explicitly approve a transaction before payment.

    If an audit trail exists, the approval
    is recorded there as well.
    """

    if transaction["status"] != "AWAITING_HUMAN_APPROVAL":
        return {
            "success": False,
            "status": transaction["status"],
            "message": "This transaction cannot be approved."
        }

    if not approved_by:
        return {
            "success": False,
            "status": "AWAITING_HUMAN_APPROVAL",
            "message": "Approval requires a valid human approver."
        }

    # Update the real transaction state
    transaction["status"] = "READY_FOR_PAYMENT"
    transaction["approved_by"] = approved_by

    # Record approval in audit trail if available
    if "audit_log" in transaction:
        add_audit_event(
            transaction["audit_log"],
            "HUMAN_APPROVAL",
            "Transaction approved by human.",
            {
                "approved_by": approved_by,
                "new_status": "READY_FOR_PAYMENT"
            }
        )

        add_audit_event(
            transaction["audit_log"],
            "TRANSACTION_STATE",
            "Transaction is now ready for payment.",
            {
                "status": "READY_FOR_PAYMENT"
            }
        )

    return {
        "success": True,
        "status": transaction["status"],
        "approved_by": approved_by,
        "message": "Transaction approved by human.",
        "transaction": transaction
    }


if __name__ == "__main__":

    demo_transaction = {
        "status": "AWAITING_HUMAN_APPROVAL",
        "product": "Midnight Abaya",
        "price": 3599,
        "audit_log": []
    }

    print("--- Before Approval ---")
    print(f"Status: {demo_transaction['status']}")

    result = approve_transaction(
        transaction=demo_transaction,
        approved_by="demo_user"
    )

    print("\n--- After Approval ---")
    print(f"Success: {result['success']}")
    print(f"Status: {result['status']}")
    print(f"Approved by: {result.get('approved_by')}")
    print(f"Message: {result['message']}")

    print("\n--- Audit Trail ---")

    for event in demo_transaction["audit_log"]:
        print(
            event["event_type"],
            "->",
            event["message"]
        )