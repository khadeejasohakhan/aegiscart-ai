from catalog_service import load_catalog


def normalize_text(value):
    """Normalize text for safe comparisons."""
    return str(value).strip().lower()


def filter_products(
    products,
    product_type,
    color,
    max_price,
    max_delivery_days
):
    """
    Apply hard buyer constraints.

    These rules are deterministic.
    AI cannot override them.
    """

    eligible = []
    rejected = []

    requested_type = normalize_text(product_type)
    requested_color = normalize_text(color)

    for product in products:
        reasons = []

        product_category = normalize_text(
            product["category"]
        )

        product_color = normalize_text(
            product["color"]
        )

        if product_category != requested_type:
            reasons.append(
                f"category does not match requested "
                f"{product_type}"
            )

        if (
            requested_color != "any"
            and product_color != requested_color
        ):
            reasons.append(
                f"color does not match requested {color}"
            )

        if product["price"] > max_price:
            reasons.append(
                "price exceeds budget"
            )

        if product["delivery_days"] > max_delivery_days:
            reasons.append(
                f"delivery takes "
                f"{product['delivery_days']} days, "
                f"which exceeds the "
                f"{max_delivery_days}-day limit"
            )

        if product["stock"] <= 0:
            reasons.append(
                "product is out of stock"
            )

        if reasons:
            rejected.append({
                "product": product["name"],
                "reasons": reasons
            })
        else:
            eligible.append(product)

    return eligible, rejected


def score_product(
    product,
    preferred_quality,
    priority
):
    """
    Score eligible products according to buyer priority.

    Hard constraints are already enforced before scoring.
    Priority only affects ranking between valid products.
    """

    quality_scores = {
        "premium": 3,
        "good": 2,
        "standard": 1
    }

    product_quality = normalize_text(
        product["quality"]
    )

    preferred_quality_normalized = normalize_text(
        preferred_quality
    )

    priority = normalize_text(priority)

    quality_score = quality_scores.get(
        product_quality,
        0
    )

    if (
        product_quality
        == preferred_quality_normalized
    ):
        quality_score += 2

    price_score = max(
        0,
        5 - (product["price"] / 1000)
    )

    delivery_score = max(
        0,
        5 - product["delivery_days"]
    )

    if priority == "quality":
        final_score = (
            quality_score * 3
            + delivery_score
            + price_score
        )

    elif priority == "price":
        final_score = (
            price_score * 3
            + quality_score
            + delivery_score
        )

    elif priority == "delivery":
        final_score = (
            delivery_score * 3
            + quality_score
            + price_score
        )

    else:
        final_score = (
            quality_score
            + price_score
            + delivery_score
        )

    return round(final_score, 2)


def recommend_product(
    product_type,
    color,
    max_price,
    max_delivery_days,
    preferred_quality,
    priority
):
    """
    Select the best valid product for the buyer mission.
    """

    catalog = load_catalog()

    eligible, rejected = filter_products(
        products=catalog["products"],
        product_type=product_type,
        color=color,
        max_price=max_price,
        max_delivery_days=max_delivery_days
    )

    scored_products = []

    for product in eligible:
        product_with_score = product.copy()

        product_with_score["score"] = score_product(
            product=product,
            preferred_quality=preferred_quality,
            priority=priority
        )

        scored_products.append(
            product_with_score
        )

    scored_products.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    selected = (
        scored_products[0]
        if scored_products
        else None
    )

    return {
        "selected": selected,
        "eligible_products": scored_products,
        "rejected_products": rejected
    }


if __name__ == "__main__":

    print("\nAEGISCART RECOMMENDATION ENGINE")
    print("--------------------------------")

    result = recommend_product(
        product_type="Abaya",
        color="Black",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium",
        priority="quality"
    )

    selected = result["selected"]

    if selected:
        print("\nSelected Product")
        print("Name:", selected["name"])
        print("Category:", selected["category"])
        print("Color:", selected["color"])
        print("Price: ₹", selected["price"], sep="")
        print("Quality:", selected["quality"])
        print("Score:", selected["score"])

    print("\nRejected Products")

    for product in result["rejected_products"]:
        print(
            product["product"],
            "->",
            ", ".join(product["reasons"])
        )