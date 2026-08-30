import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# ---------------------------------------------------------
# Make backend folder importable
# ---------------------------------------------------------

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

sys.path.insert(
    0,
    str(BACKEND_DIR)
)


# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------

ENV_PATH = PROJECT_ROOT / ".env"

load_dotenv(
    dotenv_path=ENV_PATH
)


# ---------------------------------------------------------
# Import AegisCart Services
# ---------------------------------------------------------

from agentic_checkout import (
    run_agentic_checkout
)

from approval_service import (
    approve_transaction
)

from payment_service import (
    create_payment_order,
    verify_payment
)


# ---------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------

app = FastAPI(
    title="AegisCart API",
    description=(
        "The Trust Layer for Agentic Commerce"
    ),
    version="1.0.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",

        "http://localhost:5174",
        "http://127.0.0.1:5174",

        "http://localhost:5175",
        "http://127.0.0.1:5175",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Temporary In-Memory Transaction Store
# ---------------------------------------------------------

TRANSACTIONS = {}

transaction_counter = 0


# ---------------------------------------------------------
# Request Models
# ---------------------------------------------------------

class CheckoutRequest(BaseModel):
    user_request: str


class ApprovalRequest(BaseModel):
    transaction_id: str
    approved_by: str


class PaymentCreateRequest(BaseModel):
    transaction_id: str


class PaymentVerifyRequest(BaseModel):
    transaction_id: str
    payment_id: str
    signature: str


# ---------------------------------------------------------
# Home
# ---------------------------------------------------------

@app.get("/")
def home():

    return {
        "project": "AegisCart",
        "tagline": (
            "The Trust Layer for Agentic Commerce"
        ),
        "status": "running",
        "message": (
            "AegisCart backend is operational."
        )
    }

@app.get("/transactions/{transaction_id}/receipt")
def get_transaction_receipt(transaction_id: str):
    transaction = TRANSACTIONS.get(transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    receipt = generate_decision_receipt(
        transaction
    )

    return {
        "success": True,
        "transaction_id": transaction_id,
        "receipt": receipt
    }
# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.get("/health")
def health():

    return {
        "status": "healthy"
    }


# ---------------------------------------------------------
# Public Frontend Configuration
# ---------------------------------------------------------

@app.get("/config")
def get_config():

    razorpay_key_id = os.getenv(
        "RAZORPAY_KEY_ID"
    )

    if not razorpay_key_id:

        raise HTTPException(
            status_code=500,
            detail=(
                "Razorpay Key ID "
                "is not configured."
            )
        )

    # Only public Key ID is exposed.
    # Razorpay Key Secret NEVER goes
    # to the frontend.

    return {
        "razorpay_key_id":
            razorpay_key_id
    }


# ---------------------------------------------------------
# Start Agentic Checkout
# ---------------------------------------------------------

@app.post("/checkout")
def checkout(
    request: CheckoutRequest
):

    global transaction_counter

    try:

        result = (
            run_agentic_checkout(
                request.user_request
            )
        )


        # -------------------------------------------------
        # Buyer Agent Failure
        # -------------------------------------------------

        if not result.get(
            "success"
        ):

            return {
                "success": False,
                "stage": result.get(
                    "stage",
                    "BUYER_AGENT"
                ),
                "error": result.get(
                    "error",
                    (
                        "Agentic checkout "
                        "could not continue."
                    )
                )
            }


        # -------------------------------------------------
        # Get Transaction
        # -------------------------------------------------

        transaction = result.get(
            "transaction"
        )

        if not transaction:

            raise HTTPException(
                status_code=500,
                detail=(
                    "Agentic checkout did "
                    "not return a transaction."
                )
            )


        # -------------------------------------------------
        # Validate Transaction Status
        # -------------------------------------------------

        if not transaction.get(
            "status"
        ):

            raise HTTPException(
                status_code=500,
                detail=(
                    "Transaction service returned "
                    "a transaction without status."
                )
            )


        # -------------------------------------------------
        # Generate Internal Transaction ID
        # -------------------------------------------------

        transaction_counter += 1

        transaction_id = (
            f"txn_{transaction_counter:04d}"
        )


        transaction[
            "transaction_id"
        ] = transaction_id


        # -------------------------------------------------
        # Store Transaction
        # -------------------------------------------------

        TRANSACTIONS[
            transaction_id
        ] = transaction


        # -------------------------------------------------
        # Success Response
        # -------------------------------------------------

        return {
            "success": True,

            "transaction_id":
                transaction_id,

            "mission":
                result.get(
                    "mission"
                ),

            "transaction":
                transaction,

            "receipt":
                result.get(
                    "receipt"
                )
        }


    except HTTPException:
        raise


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ---------------------------------------------------------
# Get Transaction
# ---------------------------------------------------------

@app.get(
    "/transactions/{transaction_id}"
)
def get_transaction(
    transaction_id: str
):

    transaction = TRANSACTIONS.get(
        transaction_id
    )

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail=(
                "Transaction not found."
            )
        )

    return {
        "success": True,
        "transaction_id":
            transaction_id,
        "transaction":
            transaction
    }


# ---------------------------------------------------------
# Human Approval
# ---------------------------------------------------------

@app.post("/approve")
def approve(
    request: ApprovalRequest
):

    transaction = TRANSACTIONS.get(
        request.transaction_id
    )

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail=(
                "Transaction not found."
            )
        )


    try:

        result = approve_transaction(
            transaction,
            request.approved_by
        )


        # -------------------------------------------------
        # Keep Updated Transaction Stored
        # -------------------------------------------------

        TRANSACTIONS[
            request.transaction_id
        ] = transaction


        return {
            "success":
                result.get(
                    "success",
                    False
                ),

            "transaction_id":
                request.transaction_id,

            "status":
                transaction.get(
                    "status"
                ),

            "message":
                result.get(
                    "message"
                ),

            "transaction":
                transaction
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ---------------------------------------------------------
# Create Razorpay Payment Order
# ---------------------------------------------------------

@app.post("/payment/create")
def payment_create(
    request: PaymentCreateRequest
):

    transaction = TRANSACTIONS.get(
        request.transaction_id
    )

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail=(
                "Transaction not found."
            )
        )


    try:

        result = create_payment_order(
            transaction
        )


        TRANSACTIONS[
            request.transaction_id
        ] = transaction


        return {
            "success":
                result.get(
                    "success",
                    False
                ),

            "transaction_id":
                request.transaction_id,

            "status":
                transaction.get(
                    "status"
                ),

            "order_id":
                result.get(
                    "order_id"
                ),

            "amount":
                result.get(
                    "amount"
                ),

            "currency":
                result.get(
                    "currency"
                ),

            "receipt":
                result.get(
                    "receipt"
                ),

            "message":
                result.get(
                    "message"
                ),

            "transaction":
                transaction
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )


# ---------------------------------------------------------
# Verify Razorpay Payment
# ---------------------------------------------------------

@app.post("/payment/verify")
def payment_verify(
    request: PaymentVerifyRequest
):

    transaction = TRANSACTIONS.get(
        request.transaction_id
    )

    if not transaction:

        raise HTTPException(
            status_code=404,
            detail=(
                "Transaction not found."
            )
        )


    try:

        result = verify_payment(
            transaction,

            razorpay_payment_id=
                request.payment_id,

            razorpay_signature=
                request.signature
        )


        TRANSACTIONS[
            request.transaction_id
        ] = transaction


        return {
            "success":
                result.get(
                    "success",
                    False
                ),

            "transaction_id":
                request.transaction_id,

            "status":
                transaction.get(
                    "status"
                ),

            "order_id":
                result.get(
                    "order_id"
                ),

            "payment_id":
                result.get(
                    "payment_id"
                ),

            "message":
                result.get(
                    "message"
                ),

            "transaction":
                transaction
        }


    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )