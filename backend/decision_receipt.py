from transaction_service import process_shopping_mission


def generate_decision_receipt(transaction):
    """
    Generate an explainable Agent Decision Receipt
    from the current AegisCart transaction state.
    """

    selected = transaction.get("selected_product")

    receipt = {
        "transaction_status": transaction.get(
            "status",
            "UNKNOWN"
        ),

        "merchant": transaction.get(
            "merchant"
        ),

        "selected_product": None,

        "rejected_products": transaction.get(
            "rejected_products",
            []
        ),

        "upsell_decision": transaction.get(
            "upsell_decision"
        ),

        "policy_decision": transaction.get(
            "policy_decision"
        ),

        "razorpay_order_id": transaction.get(
            "razorpay_order_id"
        ),

        "razorpay_payment_id": transaction.get(
            "razorpay_payment_id"
        ),

        "decision_timeline": []
    }


    # -----------------------------------------------------
    # Selected Product
    # -----------------------------------------------------

    if selected:
        receipt["selected_product"] = {
            "name": selected.get("name"),
            "category": selected.get("category"),
            "color": selected.get("color"),
            "price": selected.get("price"),
            "quality": selected.get("quality"),
            "delivery_days": selected.get(
                "delivery_days"
            ),
            "score": selected.get("score")
        }


    # -----------------------------------------------------
    # Decision Timeline
    # -----------------------------------------------------

    for event in transaction.get(
        "audit_log",
        []
    ):
        receipt["decision_timeline"].append({
            "event": event.get(
                "event_type"
            ),

            "message": event.get(
                "message"
            ),

            "details": event.get(
                "details",
                {}
            ),

            "timestamp": event.get(
                "timestamp"
            )
        })


    return receipt


# =========================================================
# Local Test
# =========================================================

if __name__ == "__main__":

    transaction = process_shopping_mission(
        product_type="Abaya",
        color="Black",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium",
        priority="quality",

        proposed_upsell={
            "name": "Premium Hijab",
            "price": 699
        }
    )

    receipt = generate_decision_receipt(
        transaction
    )


    print("\n================================")
    print("             AEGISCART")
    print("      AGENT DECISION RECEIPT")
    print("================================")


    # -----------------------------------------------------
    # Transaction Status
    # -----------------------------------------------------

    print(
        "\nTransaction Status:",
        receipt["transaction_status"]
    )

    print(
        "Merchant:",
        receipt["merchant"]
    )


    # -----------------------------------------------------
    # Selected Product
    # -----------------------------------------------------

    selected = receipt[
        "selected_product"
    ]

    if selected:

        print("\nSelected Product")

        print(
            "  Name:",
            selected["name"]
        )

        print(
            "  Price: ₹",
            selected["price"],
            sep=""
        )

        print(
            "  Quality:",
            selected["quality"]
        )

        print(
            "  Delivery:",
            selected["delivery_days"],
            "days"
        )

        print(
            "  Match Score:",
            selected["score"]
        )


    # -----------------------------------------------------
    # Rejected Alternatives
    # -----------------------------------------------------

    rejected_products = receipt[
        "rejected_products"
    ]

    if rejected_products:

        print("\nRejected Alternatives")

        for product in rejected_products:

            reasons = ", ".join(
                product.get(
                    "reasons",
                    []
                )
            )

            print(
                f"  {product.get('product')} "
                f"-> {reasons}"
            )


    # -----------------------------------------------------
    # Merchant Upsell
    # -----------------------------------------------------

    upsell = receipt[
        "upsell_decision"
    ]

    if upsell:

        print("\nMerchant Upsell")

        print(
            "  Item:",
            upsell.get("name")
        )

        print(
            "  Price: ₹",
            upsell.get("price"),
            sep=""
        )

        print(
            "  Percentage:",
            f"{upsell.get('percentage')}%"
        )

        print(
            "  Decision:",
            upsell.get("decision")
        )

        print(
            "  Reason:",
            upsell.get("reason")
        )


    # -----------------------------------------------------
    # Purchase Constitution
    # -----------------------------------------------------

    policy = receipt[
        "policy_decision"
    ]

    if policy:

        print("\nPurchase Constitution")

        print(
            "  Decision:",
            policy.get("decision")
        )

        print(
            "  Reason:",
            policy.get("reason")
        )


    # -----------------------------------------------------
    # Razorpay
    # -----------------------------------------------------

    if receipt["razorpay_order_id"]:

        print("\nRazorpay")

        print(
            "  Order ID:",
            receipt["razorpay_order_id"]
        )

        if receipt["razorpay_payment_id"]:

            print(
                "  Payment ID:",
                receipt[
                    "razorpay_payment_id"
                ]
            )


    # -----------------------------------------------------
    # Decision Timeline
    # -----------------------------------------------------

    print("\nDecision Timeline")

    for event in receipt[
        "decision_timeline"
    ]:

        print(
            f"  {event['event']} "
            f"-> {event['message']}"
        )


    print("\n================================")