import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.agentic_checkout import run_agentic_checkout
from backend.approval_service import approve_transaction
from backend.payment_service import create_payment_order, verify_payment


app = FastAPI(
    title="AegisCart API",
    version="1.0.0",
    description=(
        "Trust layer for agentic commerce with "
        "policy checks, human approval, and Razorpay payments."
    )
)


TRANSACTIONS = {}


class CheckoutRequest(BaseModel):
    user_request: str


class ApprovalRequest(BaseModel):
    transaction_id: str
    approved_by: str


class PaymentOrderRequest(BaseModel):
    transaction_id: str


class PaymentVerificationRequest(BaseModel):
    transaction_id: str
    razorpay_payment_id: str
    razorpay_signature: str


@app.get("/")
def root():
    return {
        "project": "AegisCart",
        "status": "running",
        "message": "AegisCart API is live."
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/checkout")
def checkout(request: CheckoutRequest):
    result = run_agentic_checkout(
        request.user_request
    )

    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result
        )

    transaction = result["transaction"]

    transaction_id = (
        transaction.get("transaction_id")
        or f"txn_{len(TRANSACTIONS) + 1:04d}"
    )

    transaction["transaction_id"] = transaction_id

    TRANSACTIONS[transaction_id] = transaction

    return {
        "success": True,
        "transaction_id": transaction_id,
        "mission": result["mission"],
        "transaction": transaction,
        "receipt": result["receipt"]
    }


@app.get("/transactions/{transaction_id}")
def get_transaction(transaction_id: str):
    transaction = TRANSACTIONS.get(
        transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    return transaction


@app.post("/approve")
def approve(request: ApprovalRequest):
    transaction = TRANSACTIONS.get(
        request.transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    return approve_transaction(
        transaction=transaction,
        approved_by=request.approved_by
    )


@app.post("/payment/create")
def create_payment(
    request: PaymentOrderRequest
):
    transaction = TRANSACTIONS.get(
        request.transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    return create_payment_order(
        transaction
    )


@app.post("/payment/verify")
def verify(
    request: PaymentVerificationRequest
):
    transaction = TRANSACTIONS.get(
        request.transaction_id
    )

    if not transaction:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found."
        )

    return verify_payment(
        transaction=transaction,
        razorpay_payment_id=(
            request.razorpay_payment_id
        ),
        razorpay_signature=(
            request.razorpay_signature
        )
    )