from catalog_service import load_catalog
from recommendation_engine import recommend_product
from policy_engine import load_policy, evaluate_purchase
from audit_service import add_audit_event


def process_shopping_mission(
    product_type,
    color,
    max_price,
    max_delivery_days,
    preferred_quality,
    priority
):
    audit_log = []

    # Record the buyer mission
    add_audit_event(
        audit_log,
        "MISSION_RECEIVED",
        "Shopping mission received.",
        {
            "product_type": product_type,
            "color": color,
            "max_price": max_price,
            "max_delivery_days": max_delivery_days,
            "preferred_quality": preferred_quality,
            "priority": priority
        }
    )

    # Load merchant catalog
    catalog = load_catalog()

    # Find the best product that satisfies hard constraints
    recommendation = recommend_product(
        product_type=product_type,
        color=color,
        max_price=max_price,
        max_delivery_days=max_delivery_days,
        preferred_quality=preferred_quality,
        priority=priority
    )

    # Record rejected products
    for rejected_product in recommendation["rejected_products"]:
        add_audit_event(
            audit_log,
            "PRODUCT_REJECTED",
            f"{rejected_product['product']} rejected.",
            {
                "product": rejected_product["product"],
                "reasons": rejected_product["reasons"]
            }
        )

    selected_product = recommendation["selected"]

    # Stop safely if nothing matches
    if selected_product is None:
        add_audit_event(
            audit_log,
            "NO_MATCH",
            "No product satisfied all buyer constraints.",
            {
                "product_type": product_type,
                "color": color,
                "priority": priority
            }
        )

        return {
            "status": "NO_MATCH",
            "merchant": catalog["merchant"]["name"],
            "recommendation": recommendation,
            "audit_log": audit_log,
            "message": "No product matched the buyer's requirements."
        }

    # Record selected product
    add_audit_event(
        audit_log,
        "PRODUCT_SELECTED",
        f"{selected_product['name']} selected.",
        {
            "product": selected_product["name"],
            "category": selected_product["category"],
            "color": selected_product["color"],
            "price": selected_product["price"],
            "quality": selected_product["quality"],
            "score": selected_product["score"],
            "priority": priority
        }
    )

    # Apply deterministic purchase policy
    policy = load_policy()

    policy_decision = evaluate_purchase(
        selected_product["price"],
        policy
    )

    add_audit_event(
        audit_log,
        "POLICY_CHECK",
        policy_decision["reason"],
        {
            "decision": policy_decision["decision"],
            "price": selected_product["price"]
        }
    )

    # Convert policy decision into transaction state
    if policy_decision["decision"] == "ALLOW":
        status = "READY_FOR_PAYMENT"

    elif policy_decision["decision"] == "REQUIRE_APPROVAL":
        status = "AWAITING_HUMAN_APPROVAL"

    else:
        status = "BLOCKED"

    return {
        "status": status,
        "merchant": catalog["merchant"]["name"],
        "selected_product": selected_product,
        "policy_decision": policy_decision,
        "rejected_products": recommendation["rejected_products"],
        "recommendation": recommendation,
        "audit_log": audit_log
    }


if __name__ == "__main__":

    transaction = process_shopping_mission(
        product_type="Abaya",
        color="Black",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium",
        priority="quality"
    )

    print("\nAEGISCART TRANSACTION SERVICE")
    print("-----------------------------")

    print("Status:", transaction["status"])
    print("Merchant:", transaction["merchant"])

    if transaction["status"] == "NO_MATCH":
        print(transaction["message"])

    else:
        selected = transaction["selected_product"]

        print("Selected Product:", selected["name"])
        print("Category:", selected["category"])
        print("Color:", selected["color"])
        print("Price: ₹", selected["price"], sep="")
        print("Quality:", selected["quality"])
        print("Score:", selected["score"])

        print(
            "Policy Decision:",
            transaction["policy_decision"]["decision"]
        )

        print(
            "Reason:",
            transaction["policy_decision"]["reason"]
        )

    print("\nAUDIT TRAIL")

    for event in transaction["audit_log"]:
        print(
            event["event_type"],
            "->",
            event["message"]
        )