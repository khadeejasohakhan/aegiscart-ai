import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

from agentic_checkout import run_agentic_checkout


def test_complete_agentic_checkout_pipeline():

    request = (
        "Find me a premium black abaya under ₹4,000 "
        "that can arrive within 2 days. "
        "Quality matters more than getting the cheapest one."
    )

    result = run_agentic_checkout(request)

    assert result["success"] is True

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