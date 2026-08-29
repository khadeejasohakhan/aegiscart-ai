from catalog_service import load_catalog


def normalize_text(value):
    return str(value).strip().lower()


def filter_products(
    products,
    product_type,
    color,
    max_price,
    max_delivery_days
):
    eligible = []
    rejected = []

    requested_type = normalize_text(product_type)
    requested_color = normalize_text(color)

    for product in products:
        reasons = []

        product_category = normalize_text(product["category"])
        product_color = normalize_text(product["color"])

        # Product type must match
        if product_category != requested_type:
            reasons.append(
                f"category '{product['category']}' does not match "
                f"requested type '{product_type}'"
            )

        # Color must match unless buyer said Any
        if requested_color != "any":
            if product_color != requested_color:
                reasons.append(
                    f"color '{product['color']}' does not match "
                    f"requested color '{color}'"
                )

        # Budget constraint
        if product["price"] > max_price:
            reasons.append(
                f"price ₹{product['price']} exceeds budget ₹{max_price}"
            )

        # Delivery constraint
        if product["delivery_days"] > max_delivery_days:
            reasons.append(
                f"delivery takes {product['delivery_days']} days, "
                f"which exceeds the {max_delivery_days}-day limit"
            )

        # Stock constraint
        if product["stock"] <= 0:
            reasons.append("product is out of stock")

        if reasons:
            rejected.append({
                "product": product["name"],
                "reasons": reasons
            })
        else:
            eligible.append(product)

    return eligible, rejected


def score_product(product, preferred_quality):
    score = 0

    # Strong reward when quality matches buyer preference
    if normalize_text(product["quality"]) == normalize_text(preferred_quality):
        score += 10

    # Slight preference for faster delivery
    score += max(
        0,
        5 - product["delivery_days"]
    )

    # Slight preference for lower price
    score += max(
        0,
        5 - (product["price"] / 1000)
    )

    return round(score, 2)


def recommend_product(
    product_type,
    color,
    max_price,
    max_delivery_days,
    preferred_quality
):
    catalog = load_catalog()

    products = catalog["products"]

    eligible, rejected = filter_products(
        products,
        product_type,
        color,
        max_price,
        max_delivery_days
    )

    scored_products = []

    for product in eligible:
        product_copy = product.copy()

        product_copy["score"] = score_product(
            product_copy,
            preferred_quality
        )

        scored_products.append(product_copy)

    scored_products.sort(
        key=lambda product: product["score"],
        reverse=True
    )

    selected = (
        scored_products[0]
        if scored_products
        else None
    )

    return {
        "selected": selected,
        "eligible": scored_products,
        "rejected": rejected
    }


if __name__ == "__main__":
    result = recommend_product(
        product_type="Abaya",
        color="Black",
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    selected = result["selected"]

    print("\nAEGISCART RECOMMENDATION ENGINE")
    print("--------------------------------")

    if selected:
        print("Selected:", selected["name"])
        print("Category:", selected["category"])
        print("Color:", selected["color"])
        print("Price: ₹", selected["price"], sep="")
        print("Quality:", selected["quality"])
        print("Score:", selected["score"])
    else:
        print("No eligible product found.")

    print("\nRejected Products:")

    for item in result["rejected"]:
        print(
            "-",
            item["product"],
            "->",
            "; ".join(item["reasons"])
        )