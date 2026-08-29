import json
from pathlib import Path


CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"


def load_catalog():
    """Load the merchant catalog from the JSON file."""

    with open(CATALOG_PATH, "r", encoding="utf-8") as file:
        catalog = json.load(file)

    return catalog


def validate_catalog(catalog):
    """Check that every product contains the fields AegisCart needs."""

    required_fields = {
        "id",
        "name",
        "category",
        "price",
        "color",
        "quality",
        "delivery_days",
        "stock"
    }

    for product in catalog.get("products", []):
        missing_fields = required_fields - product.keys()

        if missing_fields:
            raise ValueError(
                f"{product.get('name', 'Unknown product')} "
                f"is missing fields: {missing_fields}"
            )

    return True


if __name__ == "__main__":
    catalog = load_catalog()
    validate_catalog(catalog)

    print(f"Merchant: {catalog['merchant']['name']}")
    print(f"Products loaded: {len(catalog['products'])}")
    print("Catalog validation successful.")