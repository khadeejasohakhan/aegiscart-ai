def validate_mission(mission):
    """
    Validate the structured shopping mission
    before it reaches the recommendation engine.
    """

    required_fields = {
        "product_type",
        "max_price",
        "max_delivery_days",
        "preferred_quality"
    }

    missing_fields = required_fields - mission.keys()

    if missing_fields:
        return {
            "valid": False,
            "reason": f"Missing mission fields: {sorted(missing_fields)}"
        }

    if mission["max_price"] <= 0:
        return {
            "valid": False,
            "reason": "Maximum price must be greater than zero."
        }

    if mission["max_delivery_days"] <= 0:
        return {
            "valid": False,
            "reason": "Delivery days must be greater than zero."
        }

    return {
        "valid": True,
        "reason": "Mission is valid."
    }


if __name__ == "__main__":

    demo_mission = {
        "product_type": "abaya",
        "color": "black",
        "max_price": 4000,
        "max_delivery_days": 2,
        "preferred_quality": "Premium",
        "priority": "quality"
    }

    result = validate_mission(demo_mission)

    print("--- Shopping Mission ---")
    print(demo_mission)

    print("\n--- Validation ---")
    print(f"Valid: {result['valid']}")
    print(f"Reason: {result['reason']}")