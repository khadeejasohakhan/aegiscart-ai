from buyer_agent import parse_shopping_request
from transaction_service import process_shopping_mission
from decision_receipt import generate_decision_receipt


def run_agentic_checkout(user_request):
    # 1. Buyer Agent interprets natural language
    parsed = parse_shopping_request(user_request)

    if not parsed["success"]:
        return {
            "success": False,
            "stage": "BUYER_AGENT",
            "error": parsed["error"]
        }

    mission = parsed["mission"]

    # 2. Deterministic transaction engine enforces constraints
    transaction = process_shopping_mission(
        product_type=mission["product_type"],
        color=mission["color"],
        max_price=mission["max_price"],
        max_delivery_days=mission["max_delivery_days"],
        preferred_quality=mission["preferred_quality"]
    )

    # 3. Create explainable decision receipt
    receipt = generate_decision_receipt(transaction)

    return {
        "success": True,
        "mission": mission,
        "transaction": transaction,
        "receipt": receipt
    }


if __name__ == "__main__":
    print("\nAEGISCART AGENTIC CHECKOUT")
    print("--------------------------")

    user_request = input(
        "\nWhat would you like AegisCart to buy?\n> "
    )

    result = run_agentic_checkout(user_request)

    if not result["success"]:
        print("\n❌ AegisCart could not continue.")
        print("Stage:", result["stage"])
        print("Reason:", result["error"])

    else:
        mission = result["mission"]
        transaction = result["transaction"]
        receipt = result["receipt"]

        print("\n✅ BUYER INTENT")
        print("----------------")
        print("Product:", mission["product_type"])
        print("Color:", mission["color"])
        print("Budget: ₹", mission["max_price"], sep="")
        print(
            "Delivery:",
            mission["max_delivery_days"],
            "days"
        )
        print(
            "Preferred Quality:",
            mission["preferred_quality"]
        )
        print("Priority:", mission["priority"])

        print("\n🛒 COMMERCE DECISION")
        print("--------------------")

        if transaction["status"] == "NO_MATCH":
            print("Status: NO_MATCH")
            print(transaction["message"])

        else:
            selected = transaction["selected_product"]

            print("Selected:", selected["name"])
            print("Category:", selected["category"])
            print("Color:", selected["color"])
            print("Price: ₹", selected["price"], sep="")
            print("Score:", selected["score"])

            print(
                "Policy:",
                transaction["policy_decision"]["decision"]
            )

            print(
                "Transaction Status:",
                transaction["status"]
            )
            print("\n📋 AGENT DECISION RECEIPT")
            print("-------------------------")
            for event in receipt["decision_timeline"]:
                print(
                    event["event"],
                    "->",
                    event["message"]
                    )