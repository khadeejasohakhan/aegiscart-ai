import os
import json
import re
import time

from dotenv import load_dotenv
from google import genai

from mission_service import validate_mission


load_dotenv()


MODEL_NAMES = [
    "gemini-3.7-flash",
    "gemini-3.6-flash"
]

MAX_RETRIES = 3


# ---------------------------------------------------------
# Detect temporary / quota-related Gemini failures
# ---------------------------------------------------------

def is_retryable_gemini_error(error_text):
    text = error_text.lower()

    return (
        "429" in error_text
        or "resource_exhausted" in text
        or "quota" in text
        or "rate limit" in text
        or "503" in error_text
        or "unavailable" in text
        or "high demand" in text
    )


# ---------------------------------------------------------
# Gemini call with retries + model fallback
# ---------------------------------------------------------

def call_gemini_with_retry(client, prompt):

    last_error = None

    for model_name in MODEL_NAMES:

        print(f"\nTrying model: {model_name}")

        for attempt in range(MAX_RETRIES):

            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                return response

            except Exception as exc:

                last_error = exc
                error_text = str(exc)

                if not is_retryable_gemini_error(
                    error_text
                ):
                    raise

                if attempt < MAX_RETRIES - 1:

                    wait_seconds = 2 ** (
                        attempt + 1
                    )

                    print(
                        f"⚠️ {model_name} temporarily unavailable "
                        f"or rate limited. "
                        f"Retrying in {wait_seconds} seconds..."
                    )

                    time.sleep(wait_seconds)

                else:

                    print(
                        f"⚠️ {model_name} could not be used. "
                        f"Trying fallback model..."
                    )

    raise Exception(
        f"Gemini unavailable after retries: {last_error}"
    )


# ---------------------------------------------------------
# Deterministic Local Fallback Parser
# ---------------------------------------------------------

def parse_with_local_fallback(
    user_request
):

    text = user_request.lower()

    mission = {
        "product_type": "Abaya",
        "color": "Any",
        "max_price": 5000,
        "max_delivery_days": 7,
        "preferred_quality": "Good",
        "priority": "quality"
    }

    # -----------------------------------------------------
    # Product Type
    # -----------------------------------------------------

    if "abaya" in text:
        mission["product_type"] = "Abaya"

    elif "hijab" in text:
        mission["product_type"] = "Hijab"

    elif "dress" in text:
        mission["product_type"] = "Dress"

    else:
        return {
            "success": False,
            "mission": None,
            "error": (
                "The AI provider is unavailable and "
                "the local fallback could not safely "
                "identify the requested product type."
            )
        }


    # -----------------------------------------------------
    # Color
    # -----------------------------------------------------

    known_colors = [
        "black",
        "white",
        "blue",
        "red",
        "green",
        "beige",
        "brown",
        "grey",
        "gray"
    ]

    for color in known_colors:
        if color in text:

            if color == "gray":
                color = "grey"

            mission["color"] = (
                color.capitalize()
            )

            break


    # -----------------------------------------------------
    # Maximum Price
    #
    # Supports examples:
    # ₹4000
    # under 4000
    # below 4000
    # -----------------------------------------------------

    price_match = re.search(
        r"(?:₹\s*|under\s+|below\s+|less than\s+)"
        r"(\d{3,6})",
        text
    )

    if price_match:
        mission["max_price"] = int(
            price_match.group(1)
        )


    # -----------------------------------------------------
    # Delivery Days
    #
    # Examples:
    # within 2 days
    # in 3 days
    # -----------------------------------------------------

    delivery_match = re.search(
        r"(?:within|in)\s+(\d+)\s+days?",
        text
    )

    if delivery_match:
        mission[
            "max_delivery_days"
        ] = int(
            delivery_match.group(1)
        )


    # -----------------------------------------------------
    # Quality
    # -----------------------------------------------------

    if "premium" in text:
        mission[
            "preferred_quality"
        ] = "Premium"

    elif "standard" in text:
        mission[
            "preferred_quality"
        ] = "Standard"

    elif "good" in text:
        mission[
            "preferred_quality"
        ] = "Good"


    # -----------------------------------------------------
    # Priority
    # -----------------------------------------------------

    if (
        "quality matters most" in text
        or "best quality" in text
        or "quality first" in text
    ):
        mission["priority"] = "quality"

    elif (
        "cheapest" in text
        or "lowest price" in text
        or "price matters most" in text
    ):
        mission["priority"] = "price"

    elif (
        "fastest" in text
        or "delivery matters most" in text
        or "arrive fastest" in text
    ):
        mission["priority"] = "delivery"


    # -----------------------------------------------------
    # Validate using the same deterministic validator
    # -----------------------------------------------------

    is_valid, error = validate_mission(
        mission
    )

    if not is_valid:
        return {
            "success": False,
            "mission": None,
            "error": error
        }


    mission[
        "original_request"
    ] = user_request

    mission[
        "interpretation_source"
    ] = "LOCAL_FALLBACK"

    return {
        "success": True,
        "mission": mission,
        "error": None
    }


# ---------------------------------------------------------
# Main Buyer Agent
# ---------------------------------------------------------

def parse_shopping_request(
    user_request
):

    # -----------------------------------------------------
    # 1. Validate Input
    # -----------------------------------------------------

    if (
        not user_request
        or not user_request.strip()
    ):
        return {
            "success": False,
            "mission": None,
            "error": (
                "Shopping request cannot be empty."
            )
        }


    # -----------------------------------------------------
    # 2. Load Gemini API Key
    # -----------------------------------------------------

    api_key = os.getenv(
        "GEMINI_API_KEY"
    )

    # If no API key is available,
    # attempt safe local interpretation.

    if not api_key:

        print(
            "⚠️ Gemini API key unavailable. "
            "Using local fallback parser."
        )

        return parse_with_local_fallback(
            user_request
        )


    try:

        client = genai.Client(
            api_key=api_key
        )


        # -------------------------------------------------
        # 3. Buyer Agent Prompt
        # -------------------------------------------------

        prompt = f"""
You are the Buyer Agent for AegisCart.

Your job is ONLY to understand the buyer's shopping request
and convert it into structured JSON.

Buyer request:

{user_request}

Return ONLY valid JSON.

Use exactly this structure:

{{
    "product_type": "string",
    "color": "string",
    "max_price": 0,
    "max_delivery_days": 0,
    "preferred_quality": "Premium",
    "priority": "quality"
}}

Rules:

- max_price must be an integer in INR.
- max_delivery_days must be an integer.
- preferred_quality must be one of:
  Premium, Good, Standard.
- priority must be one of:
  quality, price, delivery.
- If no color is mentioned, use "Any".
- If quality matters most, priority must be "quality".
- If cheapest price matters most, priority must be "price".
- If fastest arrival matters most, priority must be "delivery".
- Do not create payment decisions.
- Do not authorize purchases.
- Do not add markdown.
- Do not add explanations outside the JSON.
"""


        # -------------------------------------------------
        # 4. Gemini Call
        # -------------------------------------------------

        response = call_gemini_with_retry(
            client,
            prompt
        )


        # -------------------------------------------------
        # 5. Clean Gemini Output
        # -------------------------------------------------

        raw_response = (
            response.text.strip()
        )

        raw_response = (
            raw_response.replace(
                "```json",
                ""
            )
        )

        raw_response = (
            raw_response.replace(
                "```",
                ""
            )
        )

        raw_response = (
            raw_response.strip()
        )


        # -------------------------------------------------
        # 6. Parse JSON
        # -------------------------------------------------

        mission = json.loads(
            raw_response
        )


        # -------------------------------------------------
        # 7. Deterministic Validation
        # -------------------------------------------------

        is_valid, error = (
            validate_mission(
                mission
            )
        )

        if not is_valid:

            return {
                "success": False,
                "mission": None,
                "error": error
            }


        mission[
            "original_request"
        ] = user_request

        mission[
            "interpretation_source"
        ] = "GEMINI"


        return {
            "success": True,
            "mission": mission,
            "error": None
        }


    # -----------------------------------------------------
    # Gemini Invalid JSON
    # -----------------------------------------------------

    except json.JSONDecodeError:

        print(
            "⚠️ Gemini returned invalid JSON. "
            "Using local fallback parser."
        )

        return parse_with_local_fallback(
            user_request
        )


    # -----------------------------------------------------
    # Gemini Error
    # -----------------------------------------------------

    except Exception as exc:

        error_text = str(exc)

        if is_retryable_gemini_error(
            error_text
        ):

            print(
                "\n⚠️ Gemini unavailable or quota exceeded."
            )

            print(
                "Switching to safe local fallback parser."
            )

            return parse_with_local_fallback(
                user_request
            )


        return {
            "success": False,
            "mission": None,
            "error": (
                f"Buyer Agent failed: {exc}"
            )
        }


# ---------------------------------------------------------
# Manual Testing
# ---------------------------------------------------------

if __name__ == "__main__":

    print(
        "\nAEGISCART BUYER AGENT"
    )

    print(
        "---------------------"
    )

    user_request = input(
        "\nWhat would you like "
        "AegisCart to buy?\n> "
    )

    result = parse_shopping_request(
        user_request
    )

    if not result["success"]:

        print(
            "\n❌ Buyer Agent Error:"
        )

        print(
            result["error"]
        )

    else:

        mission = result[
            "mission"
        ]

        print(
            "\n✅ Shopping Mission Interpreted"
        )

        print(
            "------------------------------"
        )

        print(
            "Source:",
            mission.get(
                "interpretation_source"
            )
        )

        print(
            "Product:",
            mission["product_type"]
        )

        print(
            "Color:",
            mission["color"]
        )

        print(
            "Maximum Price: ₹",
            mission["max_price"],
            sep=""
        )

        print(
            "Maximum Delivery:",
            mission[
                "max_delivery_days"
            ],
            "days"
        )

        print(
            "Preferred Quality:",
            mission[
                "preferred_quality"
            ]
        )

        print(
            "Priority:",
            mission["priority"]
        )