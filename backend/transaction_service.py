from catalog_service import load_catalog
from recommendation_engine import recommend_product
from policy_engine import load_policy, evaluate_purchase
from audit_service import add_audit_event


def process_shopping_mission(
    max_price,
    max_delivery_days,
    preferred_quality
):
    """
    Process a shopping mission from recommendation
    through financial policy evaluation.
    """

    audit_log = []

    # 1. Record the incoming mission
    add_audit_event(
        audit_log,
        "MISSION_RECEIVED",
        "Shopping mission received.",
        {
            "max_price": max_price,
            "max_delivery_days": max_delivery_days,
            "preferred_quality": preferred_quality
        }
    )

    # 2. Load merchant catalog
    catalog = load_catalog()

    # 3. Find the best eligible product
    recommendation = recommend_product(
        products=catalog["products"],
        max_price=max_price,
        max_delivery_days=max_delivery_days,
        preferred_quality=preferred_quality
    )

    selected_product = recommendation["selected"]

    # Record rejected products
    for rejected_product in recommendation["rejected"]:
        add_audit_event(
            audit_log,
            "PRODUCT_REJECTED",
            f"{rejected_product['product']} rejected.",
            {
                "product": rejected_product["product"],
                "reasons": rejected_product["reasons"]
            }
        )

    # 4. Handle case where nothing matches
    if selected_product is None:
        return {
            "status": "NO_MATCH",
            "message": "No product satisfies the shopping constraints.",
            "recommendation": recommendation,
            "audit_log": audit_log
        }
        

    # 5. Record selected product
    add_audit_event(
        audit_log,
        "PRODUCT_SELECTED",
        f"{selected_product['name']} selected as the best eligible product.",
        {
            "product": selected_product["name"],
            "price": selected_product["price"],
            "score": selected_product["score"]
        }
    )

    # 6. Load Purchase Constitution
    policy = load_policy()

    # 7. Evaluate financial authorization
    policy_result = evaluate_purchase(
        selected_product["price"],
        policy
    )

    add_audit_event(
        audit_log,
        "POLICY_CHECK",
        policy_result["reason"],
        {
            "decision": policy_result["decision"],
            "price": selected_product["price"]
        }
    )

    # 8. Determine transaction state
    if policy_result["decision"] == "ALLOW":
        transaction_status = "READY_FOR_PAYMENT"

    elif policy_result["decision"] == "REQUIRE_APPROVAL":
        transaction_status = "AWAITING_HUMAN_APPROVAL"

    else:
        transaction_status = "BLOCKED"

    # 9. Return transaction with its audit history
    return {
        "status": transaction_status,
        "merchant": catalog["merchant"]["name"],
        "selected_product": selected_product,
        "policy_decision": policy_result,
        "rejected_products": recommendation["rejected"],
        "audit_log": audit_log
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

    print("\n--- Audit Trail ---")

    for event in result["audit_log"]:
        print(
            f"{event['event_type']} -> "
            f"{event['message']}"
        )