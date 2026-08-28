from buyer_agent import parse_shopping_request
from transaction_service import process_shopping_mission
from decision_receipt import generate_decision_receipt


def run_agentic_checkout(user_request):
    """
    Run a natural-language shopping request through
    the complete AegisCart decision pipeline.
    """

    # 1. Buyer Agent interprets the request
    parsed_result = parse_shopping_request(user_request)

    if not parsed_result["success"]:
        return {
            "success": False,
            "error": parsed_result["error"]
        }

    mission = parsed_result["mission"]

    # 2. Deterministic commerce engine handles the mission
    transaction = process_shopping_mission(
        max_price=mission["max_price"],
        max_delivery_days=mission["max_delivery_days"],
        preferred_quality=mission["preferred_quality"]
    )

    # 3. Generate explainable decision receipt
    receipt = generate_decision_receipt(transaction)

    return {
        "success": True,
        "mission": mission,
        "transaction": transaction,
        "receipt": receipt
    }


if __name__ == "__main__":

    user_request = input(
        "\nWhat would you like AegisCart to buy?\n> "
    )

    result = run_agentic_checkout(user_request)

    if not result["success"]:
        print(f"\nRequest failed: {result['error']}")

    else:
        mission = result["mission"]
        transaction = result["transaction"]
        receipt = result["receipt"]

        print("\n========== AEGISCART ==========")

        print("\nInterpreted Mission")
        print(f"Product: {mission['product_type']}")
        print(f"Color: {mission.get('color', 'Not specified')}")
        print(f"Budget: ₹{mission['max_price']}")
        print(
            f"Maximum Delivery: "
            f"{mission['max_delivery_days']} days"
        )
        print(
            f"Preferred Quality: "
            f"{mission['preferred_quality']}"
        )

        print("\nRecommended Product")

        selected = receipt["selected_product"]

        if selected:
            print(f"Product: {selected['name']}")
            print(f"Price: ₹{selected['price']}")
            print(f"Quality: {selected['quality']}")
            print(f"Match Score: {selected['score']}")
        else:
            print("No suitable product found.")

        print("\nPurchase Constitution")

        policy = receipt["policy_decision"]

        if policy:
            print(f"Decision: {policy['decision']}")
            print(f"Reason: {policy['reason']}")

        print(
            f"\nTransaction Status: "
            f"{transaction['status']}"
        )

        print("\nRejected Alternatives")

        for product in receipt["rejected_products"]:
            reasons = ", ".join(product["reasons"])
            print(
                f"{product['product']} -> {reasons}"
            )

        print("\nDecision Timeline")

        for event in receipt["decision_timeline"]:
            print(
                f"{event['event']} -> "
                f"{event['message']}"
            )

        print("\n================================")