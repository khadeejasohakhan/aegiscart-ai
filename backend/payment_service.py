import os
from uuid import uuid4
from pathlib import Path

import razorpay
from dotenv import load_dotenv

from audit_service import add_audit_event


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

    if transaction.get("status") != "READY_FOR_PAYMENT":
        return {
            "success": False,
            "status": transaction.get("status"),
            "message": (
                "Payment blocked because the transaction "
                "is not ready for payment."
            )
        }

    selected_product = transaction.get("selected_product")

    if not selected_product:
        return {
            "success": False,
            "status": transaction.get("status"),
            "message": "Selected product is missing."
        }

    price_rupees = selected_product["price"]
    amount_paise = int(price_rupees * 100)

    receipt_id = f"aegis_{uuid4().hex[:12]}"

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


def verify_payment(
    transaction,
    razorpay_payment_id,
    razorpay_signature
):
    """
    Verify Razorpay payment signature.

    Payment is considered successful only
    after signature verification passes.
    """

    if transaction.get("status") != "PAYMENT_PENDING":
        return {
            "success": False,
            "status": transaction.get("status"),
            "message": (
                "Payment verification is not allowed "
                "for this transaction state."
            )
        }

    order_id = transaction.get(
        "razorpay_order_id"
    )

    if not order_id:
        return {
            "success": False,
            "status": transaction.get("status"),
            "message": (
                "Razorpay order ID is missing."
            )
        }

    verification_data = {
        "razorpay_order_id": order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }

    try:
        client = get_razorpay_client()

        client.utility.verify_payment_signature(
            verification_data
        )

    except Exception as error:

        transaction["status"] = (
            "PAYMENT_VERIFICATION_FAILED"
        )

        if "audit_log" in transaction:
            add_audit_event(
                transaction["audit_log"],
                "PAYMENT_VERIFICATION_FAILED",
                "Razorpay payment signature verification failed.",
                {
                    "razorpay_order_id": order_id,
                    "razorpay_payment_id": (
                        razorpay_payment_id
                    ),
                    "error_type": (
                        type(error).__name__
                    )
                }
            )

            add_audit_event(
                transaction["audit_log"],
                "TRANSACTION_STATE",
                "Transaction moved to payment verification failed.",
                {
                    "status": (
                        "PAYMENT_VERIFICATION_FAILED"
                    )
                }
            )

        return {
            "success": False,
            "status": transaction["status"],
            "message": (
                "Payment signature verification failed."
            )
        }

    transaction["razorpay_payment_id"] = (
        razorpay_payment_id
    )

    transaction["status"] = "PAYMENT_VERIFIED"

    if "audit_log" in transaction:

        add_audit_event(
            transaction["audit_log"],
            "PAYMENT_VERIFIED",
            "Razorpay payment signature verified successfully.",
            {
                "razorpay_order_id": order_id,
                "razorpay_payment_id": (
                    razorpay_payment_id
                )
            }
        )

        add_audit_event(
            transaction["audit_log"],
            "TRANSACTION_STATE",
            "Transaction payment has been verified.",
            {
                "status": "PAYMENT_VERIFIED"
            }
        )

    return {
        "success": True,
        "status": transaction["status"],
        "order_id": order_id,
        "payment_id": razorpay_payment_id,
        "message": (
            "Payment signature verified successfully."
        ),
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

    print("\nAUDIT TRAIL")

    for event in demo_transaction["audit_log"]:

        print(
            event["event_type"],
            "->",
            event["message"]
        )