import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

from approval_service import approve_transaction


def test_valid_human_approval():
    transaction = {
        "status": "AWAITING_HUMAN_APPROVAL"
    }

    result = approve_transaction(
        transaction,
        approved_by="demo_user"
    )

    assert result["success"] is True
    assert result["status"] == "READY_FOR_PAYMENT"


def test_missing_human_approval_is_rejected():
    transaction = {
        "status": "AWAITING_HUMAN_APPROVAL"
    }

    result = approve_transaction(
        transaction,
        approved_by=""
    )

    assert result["success"] is False
    assert result["status"] == "AWAITING_HUMAN_APPROVAL"


def test_blocked_transaction_cannot_be_approved():
    transaction = {
        "status": "BLOCKED"
    }

    result = approve_transaction(
        transaction,
        approved_by="demo_user"
    )

    assert result["success"] is False
    assert result["status"] == "BLOCKED"


def test_ai_cannot_override_blocked_transaction():
    transaction = {
        "status": "BLOCKED",
        "ai_recommendation": "Purchase immediately"
    }

    result = approve_transaction(
        transaction,
        approved_by="demo_user"
    )

    assert result["success"] is False
    assert result["status"] == "BLOCKED"