from catalog_service import load_catalog


def filter_products(products, max_price, max_delivery_days):
    """Remove products that violate hard shopping constraints."""

    eligible_products = []

    for product in products:
        if product["price"] > max_price:
            continue

        if product["delivery_days"] > max_delivery_days:
            continue

        if product["stock"] <= 0:
            continue

        eligible_products.append(product)

    return eligible_products


def score_product(product, preferred_quality):
    """
    Give products a simple deterministic score.
    Higher score = better match.
    """

    score = 0

    if product["quality"].lower() == preferred_quality.lower():
        score += 10

    # Slight preference for faster delivery
    score += max(0, 5 - product["delivery_days"])

    # Slight preference for lower price
    score += max(0, 5 - (product["price"] / 1000))

    return round(score, 2)


def recommend_product(
    products,
    max_price,
    max_delivery_days,
    preferred_quality
):
    """Return the best product plus rejected-product reasons."""

    rejected = []
    eligible = []

    for product in products:

        reasons = []

        if product["price"] > max_price:
            reasons.append("exceeds budget")

        if product["delivery_days"] > max_delivery_days:
            reasons.append("delivery is too late")

        if product["stock"] <= 0:
            reasons.append("out of stock")

        if reasons:
            rejected.append({
                "product": product["name"],
                "reasons": reasons
            })
        else:
            product_copy = product.copy()
            product_copy["score"] = score_product(
                product,
                preferred_quality
            )
            eligible.append(product_copy)

    if not eligible:
        return {
            "selected": None,
            "rejected": rejected
        }

    eligible.sort(
        key=lambda product: product["score"],
        reverse=True
    )

    return {
        "selected": eligible[0],
        "eligible": eligible,
        "rejected": rejected
    }


if __name__ == "__main__":

    catalog = load_catalog()

    result = recommend_product(
        products=catalog["products"],
        max_price=4000,
        max_delivery_days=2,
        preferred_quality="Premium"
    )

    print("\nSelected product:")

    if result["selected"]:
        selected = result["selected"]

        print(
            f"{selected['name']} | "
            f"₹{selected['price']} | "
            f"{selected['quality']} | "
            f"Score: {selected['score']}"
        )

    print("\nRejected products:")

    for item in result["rejected"]:
        print(
            f"{item['product']} -> "
            f"{', '.join(item['reasons'])}"
        )