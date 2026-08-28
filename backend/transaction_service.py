from catalog_service import load_catalog
from recommendation_engine import recommend_product
from policy_engine import load_policy, evaluate_purchase


def process_shopping_mission(
    max_price,
    max_delivery_days,
    preferred_quality
):
    """
    Process a shopping mission from recommendation
    through financial policy evaluation.
    """

    # 1. Load merchant catalog
    catalog = load_catalog()

    # 2. Find the best product
    recommendation = recommend_product(
        products=catalog["products"],
        max_price=max_price,
        max_delivery_days=max_delivery_days,
        preferred_quality=preferred_quality
    )

    selected_product = recommendation["selected"]

    if selected_product is None:
        return {
            "status": "NO_MATCH",
            "message": "No product satisfies the shopping constraints.",
            "recommendation": recommendation
        }

    # 3. Load the user's Purchase Constitution
    policy = load_policy()

    # 4. Check whether the selected purchase is financially allowed
    policy_result = evaluate_purchase(
        selected_product["price"],
        policy
    )

    # 5. Convert policy decision into transaction state
    if policy_result["decision"] == "ALLOW":
        transaction_status = "READY_FOR_PAYMENT"

    elif policy_result["decision"] == "REQUIRE_APPROVAL":
        transaction_status = "AWAITING_HUMAN_APPROVAL"

    else:
        transaction_status = "BLOCKED"

    return {
        "status": transaction_status,
        "merchant": catalog["merchant"]["name"],
        "selected_product": selected_product,
        "policy_decision": policy_result,
        "rejected_products": recommendation["rejected"]
    }


if __name__ == "__main__":

    result = process_shopping_mission(
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    print("\n--- AegisCart Transaction ---")

    print(f"Status: {result['status']}")

    if result.get("selected_product"):
        product = result["selected_product"]

        print(f"Merchant: {result['merchant']}")
        print(f"Product: {product['name']}")
        print(f"Price: ₹{product['price']}")

        print(
            "Policy decision: "
            f"{result['policy_decision']['decision']}"
        )

        print(
            "Reason: "
            f"{result['policy_decision']['reason']}"
        )