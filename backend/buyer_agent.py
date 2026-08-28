from mission_service import validate_mission


def parse_shopping_request(user_request):
    """
    Temporary Buyer Agent parser.

    This simulates the structured output that will later
    come from an LLM.
    """

    # Temporary structured response for our demo scenario
    mission = {
        "product_type": "abaya",
        "color": "black",
        "max_price": 4000,
        "max_delivery_days": 2,
        "preferred_quality": "Premium",
        "priority": "quality",
        "original_request": user_request
    }

    validation = validate_mission(mission)

    if not validation["valid"]:
        return {
            "success": False,
            "mission": None,
            "error": validation["reason"]
        }

    return {
        "success": True,
        "mission": mission,
        "error": None
    }


if __name__ == "__main__":

    user_request = (
        "Find me a premium black abaya under ₹4,000 "
        "that can arrive within 2 days. "
        "Quality matters more than getting the cheapest one."
    )

    result = parse_shopping_request(user_request)

    print("\n--- User Request ---")
    print(user_request)

    print("\n--- Buyer Agent Output ---")

    if result["success"]:
        mission = result["mission"]

        for key, value in mission.items():
            print(f"{key}: {value}")

    else:
        print(f"Mission parsing failed: {result['error']}")