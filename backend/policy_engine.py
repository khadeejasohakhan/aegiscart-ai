import json
from pathlib import Path


POLICY_PATH = (
    Path(__file__).parent.parent
    / "data"
    / "user_policy.json"
)


def load_policy():
    """Load the user's Purchase Constitution."""

    with open(
        POLICY_PATH,
        "r",
        encoding="utf-8"
    ) as file:
        return json.load(file)


def evaluate_purchase(price, policy):
    """
    Decide whether a purchase can happen automatically,
    requires human approval, or must be blocked.
    """

    autonomous_limit = policy[
        "autonomous_spend_limit"
    ]

    approval_limit = policy[
        "approval_limit"
    ]

    if price <= autonomous_limit:
        return {
            "decision": "ALLOW",
            "reason": (
                "Purchase is within the "
                "autonomous spending limit."
            )
        }

    if price <= approval_limit:
        return {
            "decision": "REQUIRE_APPROVAL",
            "reason": (
                "Purchase exceeds the "
                "autonomous spending limit."
            )
        }

    return {
        "decision": "BLOCK",
        "reason": (
            "Purchase exceeds the maximum "
            "allowed spending limit."
        )
    }


def evaluate_upsell(
    base_price,
    upsell_price,
    policy
):
    """
    Check whether a merchant upsell is within
    the user's allowed percentage.
    """

    max_percentage = policy[
        "max_upsell_percentage"
    ]

    if base_price <= 0:
        return {
            "decision": "BLOCK",
            "reason": "Invalid base product price."
        }

    upsell_percentage = (
        upsell_price / base_price
    ) * 100

    if upsell_percentage <= max_percentage:
        return {
            "decision": "ALLOW",
            "reason": (
                f"Upsell is "
                f"{upsell_percentage:.1f}% "
                f"of the base purchase, "
                f"within the "
                f"{max_percentage}% limit."
            ),
            "upsell_percentage": round(
                upsell_percentage,
                1
            )
        }

    return {
        "decision": "BLOCK",
        "reason": (
            f"Upsell is "
            f"{upsell_percentage:.1f}% "
            f"of the base purchase, "
            f"exceeding the "
            f"{max_percentage}% limit."
        ),
        "upsell_percentage": round(
            upsell_percentage,
            1
        )
    }


if __name__ == "__main__":

    policy = load_policy()

    print("\nAEGISCART PURCHASE POLICY")
    print("-------------------------")

    test_prices = [
        800,
        3599,
        6000
    ]

    for price in test_prices:

        result = evaluate_purchase(
            price,
            policy
        )

        print(
            f"₹{price} -> "
            f"{result['decision']} | "
            f"{result['reason']}"
        )

    print("\nUpsell Test")
    print("-----------")

    upsell_result = evaluate_upsell(
        base_price=3599,
        upsell_price=699,
        policy=policy
    )

    print(
        "₹699 upsell on ₹3599 ->",
        upsell_result["decision"]
    )

    print(
        "Percentage:",
        f"{upsell_result['upsell_percentage']}%"
    )

    print(
        "Reason:",
        upsell_result["reason"]
    )