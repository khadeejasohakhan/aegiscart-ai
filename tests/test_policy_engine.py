import sys
from pathlib import Path

# Allow tests to import files from the backend folder
BACKEND_PATH = Path(__file__).parent.parent / "backend"
sys.path.append(str(BACKEND_PATH))

from policy_engine import evaluate_purchase, evaluate_upsell


TEST_POLICY = {
    "autonomous_spend_limit": 1000,
    "approval_limit": 5000,
    "max_upsell_percentage": 10
}


def test_autonomous_purchase():
    result = evaluate_purchase(800, TEST_POLICY)
    assert result["decision"] == "ALLOW"


def test_purchase_requires_approval():
    result = evaluate_purchase(3599, TEST_POLICY)
    assert result["decision"] == "REQUIRE_APPROVAL"


def test_purchase_above_limit_is_blocked():
    result = evaluate_purchase(6000, TEST_POLICY)
    assert result["decision"] == "BLOCK"


def test_excessive_upsell_is_blocked():
    result = evaluate_upsell(
        base_price=3599,
        upsell_price=699,
        policy=TEST_POLICY
    )

    assert result["decision"] == "BLOCK"