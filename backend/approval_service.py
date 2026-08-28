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

    return {
        "success": True,
        "status": "READY_FOR_PAYMENT",
        "approved_by": approved_by,
        "message": "Transaction approved by human."
    }


if __name__ == "__main__":

    demo_transaction = {
        "status": "AWAITING_HUMAN_APPROVAL",
        "product": "Midnight Abaya",
        "price": 3599
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