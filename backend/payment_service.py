import os
from uuid import uuid4

import razorpay
from dotenv import load_dotenv

from audit_service import add_audit_event


from pathlib import Path

ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)


def get_razorpay_client():
    """
    Create Razorpay client using Test Mode
    credentials stored safely in .env.
    """

    key_id = os.getenv("RAZORPAY_KEY_ID")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET")

    if not key_id or not key_secret:
        raise ValueError(
            "Razorpay credentials are missing from .env."
        )

    return razorpay.Client(
        auth=(key_id, key_secret)
    )


def create_payment_order(transaction):
    """
    Create a Razorpay order only after
    AegisCart has authorised the transaction.
    """

    # Safety gate:
    # Razorpay cannot be called before authorization.
    if transaction.get("status") != "READY_FOR_PAYMENT":
        return {
            "success": False,
            "status": transaction.get("status"),
            "message": (
                "Payment blocked because the transaction "
                "is not ready for payment."
            )
        }

    selected_product = transaction.get(
        "selected_product"
    )

    if not selected_product:
        return {
            "success": False,
            "status": transaction.get("status"),
            "message": "Selected product is missing."
        }

    price_rupees = selected_product["price"]

    # Razorpay expects the amount in paise.
    # ₹3599 -> 359900
    amount_paise = int(price_rupees * 100)

    receipt_id = (
        f"aegis_{uuid4().hex[:12]}"
    )

    order_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt_id,
        "notes": {
            "project": "AegisCart",
            "merchant": transaction.get(
                "merchant",
                "Unknown"
            ),
            "product": selected_product["name"]
        }
    }

    try:
        client = get_razorpay_client()

        razorpay_order = client.order.create(
            data=order_data
        )

    except Exception as error:

        if "audit_log" in transaction:
            add_audit_event(
                transaction["audit_log"],
                "PAYMENT_ORDER_FAILED",
                "Razorpay order creation failed.",
                {
                    "error_type": type(error).__name__
                }
            )

        return {
            "success": False,
            "status": transaction.get("status"),
            "message": (
                "Razorpay order could not be created."
            ),
            "error": str(error)
        }

    # Save Razorpay information in transaction
    transaction["razorpay_order_id"] = (
        razorpay_order["id"]
    )

    transaction["payment_amount"] = (
        razorpay_order["amount"]
    )

    transaction["payment_currency"] = (
        razorpay_order["currency"]
    )

    transaction["status"] = "PAYMENT_PENDING"

    # Record payment creation
    if "audit_log" in transaction:

        add_audit_event(
            transaction["audit_log"],
            "PAYMENT_ORDER_CREATED",
            "Razorpay payment order created.",
            {
                "razorpay_order_id": (
                    razorpay_order["id"]
                ),
                "amount_paise": (
                    razorpay_order["amount"]
                ),
                "currency": (
                    razorpay_order["currency"]
                )
            }
        )

        add_audit_event(
            transaction["audit_log"],
            "TRANSACTION_STATE",
            "Transaction moved to payment pending.",
            {
                "status": "PAYMENT_PENDING"
            }
        )

    return {
        "success": True,
        "status": transaction["status"],
        "order_id": razorpay_order["id"],
        "amount": razorpay_order["amount"],
        "currency": razorpay_order["currency"],
        "receipt": razorpay_order.get("receipt"),
        "transaction": transaction
    }


if __name__ == "__main__":

    demo_transaction = {
        "status": "READY_FOR_PAYMENT",
        "merchant": "Luma",
        "selected_product": {
            "name": "Midnight Abaya",
            "price": 3599
        },
        "audit_log": []
    }

    result = create_payment_order(
        demo_transaction
    )

    print("\nAEGISCART PAYMENT SERVICE")
    print("-------------------------")

    print("Success:", result["success"])
    print("Status:", result["status"])

    if result["success"]:

        print(
            "Order ID:",
            result["order_id"]
        )

        print(
            "Amount:",
            result["amount"]
        )

        print(
            "Currency:",
            result["currency"]
        )

    else:

        print(
            "Message:",
            result["message"]
        )

        if result.get("error"):
            print(
                "Error:",
                result["error"]
            )

    print("\nAUDIT TRAIL")

    for event in demo_transaction["audit_log"]:

        print(
            event["event_type"],
            "->",
            event["message"]
        )