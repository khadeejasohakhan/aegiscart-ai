import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

from transaction_service import process_shopping_mission


def test_standard_mission_requires_approval():
    result = process_shopping_mission(
        product_type="Abaya",
        color="Black",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    assert result["selected_product"]["name"] == "Midnight Abaya"
    assert result["status"] == "AWAITING_HUMAN_APPROVAL"
    assert result["policy_decision"]["decision"] == "REQUIRE_APPROVAL"


def test_transaction_creates_audit_trail():
    result = process_shopping_mission(
        product_type="Abaya",
        color="Black",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    event_types = [
        event["event_type"]
        for event in result["audit_log"]
    ]

    assert "MISSION_RECEIVED" in event_types
    assert "PRODUCT_SELECTED" in event_types
    assert "POLICY_CHECK" in event_types


def test_no_matching_product_due_to_budget():
    result = process_shopping_mission(
        product_type="Abaya",
        color="Black",
        max_price=500,
        max_delivery_days=1,
        preferred_quality="Premium"
    )

    assert result["status"] == "NO_MATCH"
    assert result["recommendation"]["selected"] is None


def test_wrong_product_type_returns_no_match():
    result = process_shopping_mission(
        product_type="Sneakers",
        color="White",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    assert result["status"] == "NO_MATCH"
    assert result["recommendation"]["selected"] is None


def test_wrong_color_returns_no_match():
    result = process_shopping_mission(
        product_type="Abaya",
        color="White",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    assert result["status"] == "NO_MATCH"
    assert result["recommendation"]["selected"] is None