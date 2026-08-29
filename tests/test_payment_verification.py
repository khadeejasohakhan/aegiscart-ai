import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

import payment_service


class FakeUtilitySuccess:
    def verify_payment_signature(self, data):
        return True


class FakeClientSuccess:
    def __init__(self):
        self.utility = FakeUtilitySuccess()


class FakeUtilityFailure:
    def verify_payment_signature(self, data):
        raise ValueError("Invalid payment signature")


class FakeClientFailure:
    def __init__(self):
        self.utility = FakeUtilityFailure()


def test_valid_payment_signature_is_verified(monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "get_razorpay_client",
        lambda: FakeClientSuccess()
    )

    transaction = {
        "status": "PAYMENT_PENDING",
        "razorpay_order_id": "order_test123",
        "audit_log": []
    }

    result = payment_service.verify_payment(
        transaction=transaction,
        razorpay_payment_id="pay_test123",
        razorpay_signature="valid_signature"
    )

    assert result["success"] is True
    assert result["status"] == "PAYMENT_VERIFIED"
    assert transaction["status"] == "PAYMENT_VERIFIED"
    assert transaction["razorpay_payment_id"] == "pay_test123"

    event_types = [
        event["event_type"]
        for event in transaction["audit_log"]
    ]

    assert "PAYMENT_VERIFIED" in event_types
    assert "TRANSACTION_STATE" in event_types


def test_invalid_payment_signature_is_rejected(monkeypatch):
    monkeypatch.setattr(
        payment_service,
        "get_razorpay_client",
        lambda: FakeClientFailure()
    )

    transaction = {
        "status": "PAYMENT_PENDING",
        "razorpay_order_id": "order_test123",
        "audit_log": []
    }

    result = payment_service.verify_payment(
        transaction=transaction,
        razorpay_payment_id="pay_fake123",
        razorpay_signature="fake_signature"
    )

    assert result["success"] is False
    assert result["status"] == "PAYMENT_VERIFICATION_FAILED"
    assert transaction["status"] == "PAYMENT_VERIFICATION_FAILED"

    event_types = [
        event["event_type"]
        for event in transaction["audit_log"]
    ]

    assert "PAYMENT_VERIFICATION_FAILED" in event_types
    assert "TRANSACTION_STATE" in event_types


def test_payment_cannot_be_verified_before_order_creation():
    transaction = {
        "status": "READY_FOR_PAYMENT",
        "audit_log": []
    }

    result = payment_service.verify_payment(
        transaction=transaction,
        razorpay_payment_id="pay_test123",
        razorpay_signature="signature"
    )

    assert result["success"] is False
    assert result["status"] == "READY_FOR_PAYMENT"


def test_missing_order_id_blocks_verification():
    transaction = {
        "status": "PAYMENT_PENDING",
        "audit_log": []
    }

    result = payment_service.verify_payment(
        transaction=transaction,
        razorpay_payment_id="pay_test123",
        razorpay_signature="signature"
    )

    assert result["success"] is False
    assert result["status"] == "PAYMENT_PENDING"
    assert result["message"] == "Razorpay order ID is missing."