from buyer_agent import parse_shopping_request
from transaction_service import process_shopping_mission
from decision_receipt import generate_decision_receipt

def run_agentic_checkout(user_request):
    parsed = parse_shopping_request(
        user_request
    )

    # -----------------------------------------------------
    # Buyer Agent failed
    # -----------------------------------------------------

    if not parsed["success"]:
        return {
            "success": False,
            "stage": "BUYER_AGENT",
            "error": parsed["error"]
        }

    mission = parsed["mission"]


    # -----------------------------------------------------
    # Demo Merchant Upsell
    #
    # Luma proposes a Premium Hijab after the
    # buyer's main product has been understood.
    # -----------------------------------------------------

    merchant_upsell = {
        "name": "Premium Hijab",
        "price": 699
    }


    # -----------------------------------------------------
    # Process Shopping Mission
    # -----------------------------------------------------

    transaction = process_shopping_mission(
        product_type=mission["product_type"],
        color=mission["color"],
        max_price=mission["max_price"],
        max_delivery_days=mission[
            "max_delivery_days"
        ],
        preferred_quality=mission[
            "preferred_quality"
        ],
        priority=mission["priority"],

        proposed_upsell=merchant_upsell
    )


    # -----------------------------------------------------
    # Generate Explainable Decision Receipt
    # -----------------------------------------------------

    receipt = generate_decision_receipt(
        transaction
    )


    return {
        "success": True,
        "mission": mission,
        "transaction": transaction,
        "receipt": receipt
    }