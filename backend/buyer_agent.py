import os
import json
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


def call_gemini_with_retry(client, prompt):
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
                error_text = str(exc)

                is_temporary_error = (
                    "503" in error_text
                    or "UNAVAILABLE" in error_text
                    or "high demand" in error_text.lower()
                )

                if not is_temporary_error:
                    raise

                if attempt < MAX_RETRIES - 1:
                    wait_seconds = 2 ** (attempt + 1)

                    print(
                        f"⚠️ {model_name} unavailable. "
                        f"Retrying in {wait_seconds} seconds..."
                    )

                    time.sleep(wait_seconds)

                else:
                    print(
                        f"⚠️ {model_name} still unavailable. "
                        f"Trying fallback model..."
                    )

    raise Exception(
        "All configured Gemini models are temporarily unavailable."
    )


def parse_shopping_request(user_request):

    # -----------------------------
    # 1. Validate user input
    # -----------------------------

    if not user_request or not user_request.strip():
        return {
            "success": False,
            "mission": None,
            "error": "Shopping request cannot be empty."
        }

    # -----------------------------
    # 2. Load API key
    # -----------------------------

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return {
            "success": False,
            "mission": None,
            "error": "Gemini API key is missing."
        }

    try:
        client = genai.Client(api_key=api_key)

        # -----------------------------
        # 3. Buyer Agent prompt
        # -----------------------------

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

        # -----------------------------
        # 4. Gemini call with retries
        # -----------------------------

        response = call_gemini_with_retry(
            client,
            prompt
        )

        raw_response = response.text.strip()

        # -----------------------------
        # 5. Clean accidental Markdown
        # -----------------------------

        raw_response = raw_response.replace(
            "```json",
            ""
        )

        raw_response = raw_response.replace(
            "```",
            ""
        )

        raw_response = raw_response.strip()

        # -----------------------------
        # 6. Convert JSON into Python
        # -----------------------------

        mission = json.loads(raw_response)

        # -----------------------------
        # 7. Our deterministic validation
        # -----------------------------

        is_valid, error = validate_mission(
            mission
        )

        if not is_valid:
            return {
                "success": False,
                "mission": None,
                "error": error
            }

        mission["original_request"] = (
            user_request
        )

        return {
            "success": True,
            "mission": mission,
            "error": None
        }

    except json.JSONDecodeError:
        return {
            "success": False,
            "mission": None,
            "error":
                "Gemini returned invalid JSON. "
                "No shopping action was taken."
        }

    except Exception as exc:
        error_text = str(exc)

        if (
            "503" in error_text
            or "UNAVAILABLE" in error_text
            or "high demand" in error_text.lower()
        ):
            return {
                "success": False,
                "mission": None,
                "error":
                    "Buyer Agent is temporarily unavailable "
                    "after multiple retry attempts. "
                    "No shopping action was taken."
            }

        return {
            "success": False,
            "mission": None,
            "error":
                f"Buyer Agent failed: {exc}"
        }


if __name__ == "__main__":

    print("\nAEGISCART BUYER AGENT")
    print("---------------------")

    user_request = input(
        "\nWhat would you like AegisCart to buy?\n> "
    )

    result = parse_shopping_request(
        user_request
    )

    if not result["success"]:

        print("\n❌ Buyer Agent Error:")
        print(result["error"])

    else:

        mission = result["mission"]

        print(
            "\n✅ Shopping Mission Interpreted"
        )

        print(
            "------------------------------"
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
            mission["max_delivery_days"],
            "days"
        )

        print(
            "Preferred Quality:",
            mission["preferred_quality"]
        )

        print(
            "Priority:",
            mission["priority"]
        )