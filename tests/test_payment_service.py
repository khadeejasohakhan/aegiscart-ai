import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

import payment_service


class FakeOrderClient:
    def create(self, data):
        return {
            "id": "order_test123",
            "amount": data["amount"],
            "currency": data["currency"],
            "receipt": data["receipt"]
        }


class FakeRazorpayClient:
    def __init__(self):
        self.order = FakeOrderClient()


def test_payment_blocked_before_human_approval():
    transaction = {
        "status": "AWAITING_HUMAN_APPROVAL",
        "selected_product": {
            "name": "Midnight Abaya",
            "price": 3599
        },
        "audit_log": []
    }

    result = payment_service.create_payment_order(
        transaction
    )

    assert result["success"] is False
    assert result["status"] == "AWAITING_HUMAN_APPROVAL"
    assert transaction["status"] == "AWAITING_HUMAN_APPROVAL"


def test_blocked_transaction_cannot_create_payment():
    transaction = {
        "status": "BLOCKED",
        "selected_product": {
            "name": "Expensive Product",
            "price": 6000
        },
        "audit_log": []
    }

    result = payment_service.create_payment_order(
        transaction
    )

    assert result["success"] is False
    assert result["status"] == "BLOCKED"
    assert transaction["status"] == "BLOCKED"


def test_ready_transaction_can_create_payment(monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "get_razorpay_client",
        lambda: FakeRazorpayClient()
    )

    transaction = {
        "status": "READY_FOR_PAYMENT",
        "merchant": "Luma",
        "selected_product": {
            "name": "Midnight Abaya",
            "price": 3599
        },
        "audit_log": []
    }

    result = payment_service.create_payment_order(
        transaction
    )

    assert result["success"] is True
    assert result["status"] == "PAYMENT_PENDING"
    assert result["order_id"] == "order_test123"
    assert result["amount"] == 359900
    assert result["currency"] == "INR"

    assert transaction["status"] == "PAYMENT_PENDING"
    assert transaction["razorpay_order_id"] == "order_test123"


def test_payment_creation_is_recorded_in_audit(monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "get_razorpay_client",
        lambda: FakeRazorpayClient()
    )

    transaction = {
        "status": "READY_FOR_PAYMENT",
        "merchant": "Luma",
        "selected_product": {
            "name": "Midnight Abaya",
            "price": 3599
        },
        "audit_log": []
    }

    result = payment_service.create_payment_order(
        transaction
    )

    assert result["success"] is True

    event_types = [
        event["event_type"]
        for event in transaction["audit_log"]
    ]

    assert "PAYMENT_ORDER_CREATED" in event_types
    assert "TRANSACTION_STATE" in event_types


def test_missing_product_blocks_payment():
    transaction = {
        "status": "READY_FOR_PAYMENT",
        "audit_log": []
    }

    result = payment_service.create_payment_order(
        transaction
    )

    assert result["success"] is False
    assert result["message"] == "Selected product is missing."