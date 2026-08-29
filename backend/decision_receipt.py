from transaction_service import process_shopping_mission


def generate_decision_receipt(transaction):
    """Generate an explainable summary of an AegisCart decision."""

    selected = transaction.get("selected_product")

    receipt = {
        "transaction_status": transaction["status"],
        "selected_product": None,
        "rejected_products": transaction.get(
            "rejected_products",
            []
        ),
        "policy_decision": transaction.get(
            "policy_decision"
        ),
        "decision_timeline": []
    }

    if selected:
        receipt["selected_product"] = {
            "name": selected["name"],
            "price": selected["price"],
            "quality": selected["quality"],
            "score": selected["score"]
        }

    for event in transaction["audit_log"]:
        receipt["decision_timeline"].append({
            "event": event["event_type"],
            "message": event["message"],
            "details": event["details"]
        })

    return receipt


if __name__ == "__main__":

    transaction = process_shopping_mission(
    product_type="Abaya",
    color="Black",
    max_price=4000,
    max_delivery_days=2,
    preferred_quality="Premium"
)

    receipt = generate_decision_receipt(transaction)

    print("\n========== AEGISCART ==========")
    print("       AGENT DECISION RECEIPT")
    print("================================")

    print(
        f"\nTransaction Status: "
        f"{receipt['transaction_status']}"
    )

    selected = receipt["selected_product"]

    if selected:
        print("\nSelected Product")
        print(f"  {selected['name']}")
        print(f"  Price: ₹{selected['price']}")
        print(f"  Quality: {selected['quality']}")
        print(f"  Match Score: {selected['score']}")

    print("\nRejected Alternatives")

    for product in receipt["rejected_products"]:
        reasons = ", ".join(product["reasons"])

        print(
            f"  {product['product']} -> {reasons}"
        )

    policy = receipt["policy_decision"]

    if policy:
        print("\nPurchase Constitution")

        print(
            f"  Decision: {policy['decision']}"
        )

        print(
            f"  Reason: {policy['reason']}"
        )

    print("\nDecision Timeline")

    for event in receipt["decision_timeline"]:
        print(
            f"  {event['event']} -> "
            f"{event['message']}"
        )

    print("\n================================")