import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

import agentic_checkout


def test_complete_agentic_checkout_pipeline(monkeypatch):

    fake_buyer_agent_response = {
        "success": True,
        "mission": {
            "product_type": "Abaya",
            "color": "Black",
            "max_price": 4000,
            "max_delivery_days": 2,
            "preferred_quality": "Premium",
            "priority": "quality",
            "original_request": (
                "Find me a premium black abaya under ₹4,000 "
                "that can arrive within 2 days."
            )
        }
    }

    def fake_parse_shopping_request(user_request):
        return fake_buyer_agent_response

    monkeypatch.setattr(
        agentic_checkout,
        "parse_shopping_request",
        fake_parse_shopping_request
    )

    request = (
        "Find me a premium black abaya under ₹4,000 "
        "that can arrive within 2 days. "
        "Quality matters more than getting the cheapest one."
    )

    result = agentic_checkout.run_agentic_checkout(request)

    assert result["success"] is True

    assert result["mission"]["product_type"] == "Abaya"
    assert result["mission"]["color"] == "Black"
    assert result["mission"]["max_price"] == 4000
    assert result["mission"]["max_delivery_days"] == 2

    assert (
        result["transaction"]["selected_product"]["name"]
        == "Midnight Abaya"
    )

    assert (
        result["transaction"]["status"]
        == "AWAITING_HUMAN_APPROVAL"
    )

    assert (
        result["receipt"]["policy_decision"]["decision"]
        == "REQUIRE_APPROVAL"
    )


def test_checkout_stops_when_buyer_agent_fails(monkeypatch):

    fake_failure = {
        "success": False,
        "error": "Buyer Agent temporarily unavailable."
    }

    def fake_parse_shopping_request(user_request):
        return fake_failure

    monkeypatch.setattr(
        agentic_checkout,
        "parse_shopping_request",
        fake_parse_shopping_request
    )

    result = agentic_checkout.run_agentic_checkout(
        "Buy me a black abaya."
    )

    assert result["success"] is False
    assert result["stage"] == "BUYER_AGENT"
    assert "temporarily unavailable" in result["error"]