import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";


// ---------------------------------------------------------
// Load Razorpay Checkout Script
// ---------------------------------------------------------

function loadRazorpayScript() {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const script = document.createElement("script");

    script.src =
      "https://checkout.razorpay.com/v1/checkout.js";

    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);

    document.body.appendChild(script);
  });
}


// ---------------------------------------------------------
// App
// ---------------------------------------------------------

function App() {
  const [request, setRequest] = useState("");

  const [result, setResult] = useState(null);

  const [loading, setLoading] = useState(false);
  const [approving, setApproving] = useState(false);
  const [paying, setPaying] = useState(false);

  const [error, setError] = useState("");

  const [paymentMessage, setPaymentMessage] =
    useState("");

  const [liveReceipt, setLiveReceipt] =
    useState(null);

  const [receiptLoading, setReceiptLoading] =
    useState(false);


  // -------------------------------------------------------
  // Start Agentic Checkout
  // -------------------------------------------------------

  const handleCheckout = async () => {
    if (!request.trim()) {
      setError(
        "Please enter a shopping request first."
      );

      return;
    }

    setLoading(true);
    setResult(null);
    setError("");
    setPaymentMessage("");

    try {
      const response = await fetch(
        `${API_URL}/checkout`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            user_request: request,
          }),
        }
      );

      const data = await response.json();

      console.log(
        "AegisCart checkout response:",
        data
      );


      // HTTP failure

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Checkout request failed."
        );
      }


      // Buyer agent / backend workflow failure

      if (!data.success) {
        throw new Error(
          data.error ||
            data.message ||
            "AegisCart could not process this request."
        );
      }


      // Successful transaction

      setResult(data);

    } catch (err) {
      console.error(
        "Checkout error:",
        err
      );

      setError(
        err.message ||
          "AegisCart could not process this request."
      );

    } finally {
      setLoading(false);
    }
  };


  // -------------------------------------------------------
  // Human Approval
  // -------------------------------------------------------

  const handleApproval = async () => {
    if (!result?.transaction_id) {
      setError(
        "Transaction ID is missing."
      );

      return;
    }

    setApproving(true);
    setError("");

    try {
      const response = await fetch(
        `${API_URL}/approve`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify({
            transaction_id:
              result.transaction_id,

            approved_by: "demo_user",
          }),
        }
      );

      const data = await response.json();

      console.log(
        "Approval response:",
        data
      );

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Approval request failed."
        );
      }

      if (!data.success) {
        throw new Error(
          data.message ||
            "Purchase could not be approved."
        );
      }

      setResult((previous) => ({
        ...previous,

        transaction:
          data.transaction,
      }));

    } catch (err) {
      console.error(
        "Approval error:",
        err
      );

      setError(
        err.message ||
          "Human approval failed."
      );

    } finally {
      setApproving(false);
    }
  };


  // -------------------------------------------------------
  // Razorpay Payment
  // -------------------------------------------------------

  const handlePayment = async () => {
    if (!result?.transaction_id) {
      setError(
        "Transaction ID is missing."
      );

      return;
    }

    setPaying(true);
    setError("");
    setPaymentMessage("");

    try {

      // ---------------------------------------------------
      // 1. Load Razorpay Checkout
      // ---------------------------------------------------

      const loaded =
        await loadRazorpayScript();

      if (!loaded) {
        throw new Error(
          "Razorpay Checkout could not be loaded."
        );
      }


      // ---------------------------------------------------
      // 2. Get Public Razorpay Key
      // ---------------------------------------------------

      const configResponse =
        await fetch(
          `${API_URL}/config`
        );

      const config =
        await configResponse.json();

      if (
        !configResponse.ok ||
        !config.razorpay_key_id
      ) {
        throw new Error(
          config.detail ||
            "Razorpay configuration could not be loaded."
        );
      }


      // ---------------------------------------------------
      // 3. Create Razorpay Order
      // ---------------------------------------------------

      const orderResponse =
        await fetch(
          `${API_URL}/payment/create`,
          {
            method: "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              transaction_id:
                result.transaction_id,
            }),
          }
        );

      const orderData =
        await orderResponse.json();

      console.log(
        "Payment order response:",
        orderData
      );

      if (!orderResponse.ok) {
        throw new Error(
          orderData.detail ||
            "Could not create Razorpay order."
        );
      }

      if (!orderData.success) {
        throw new Error(
          orderData.message ||
            "Payment order could not be created."
        );
      }

      if (!orderData.order_id) {
        throw new Error(
          "Razorpay order ID was not returned."
        );
      }


      // ---------------------------------------------------
      // Update UI to PAYMENT_PENDING
      // ---------------------------------------------------

      if (orderData.transaction) {
        setResult((previous) => ({
          ...previous,

          transaction:
            orderData.transaction,
        }));
      }


      // ---------------------------------------------------
      // 4. Razorpay Checkout Options
      // ---------------------------------------------------

      const options = {
        key: config.razorpay_key_id,

        amount: orderData.amount,

        currency:
          orderData.currency || "INR",

        name: "AegisCart",

        description:
          result.transaction
            ?.selected_product
            ?.name ||
          "Agentic Commerce Purchase",

        order_id:
          orderData.order_id,


        // -------------------------------------------------
        // Razorpay Success Callback
        // -------------------------------------------------

        handler: async function (
          razorpayResponse
        ) {
          try {
            console.log(
              "Razorpay success callback received"
            );

            const verifyResponse =
              await fetch(
                `${API_URL}/payment/verify`,
                {
                  method: "POST",

                  headers: {
                    "Content-Type":
                      "application/json",
                  },

                  body: JSON.stringify({
                    transaction_id:
                      result.transaction_id,

                    payment_id:
                      razorpayResponse
                        .razorpay_payment_id,

                    signature:
                      razorpayResponse
                        .razorpay_signature,
                  }),
                }
              );

            const verifyData =
              await verifyResponse.json();

            console.log(
              "Verification response:",
              verifyData
            );

            if (!verifyResponse.ok) {
              throw new Error(
                verifyData.detail ||
                  "Payment verification request failed."
              );
            }

            if (!verifyData.success) {
              throw new Error(
                verifyData.message ||
                  "Payment signature could not be verified."
              );
            }

            setResult((previous) => ({
              ...previous,

              transaction:
                verifyData.transaction,
            }));

            setPaymentMessage(
              "✓ Razorpay payment signature verified securely."
            );

          } catch (err) {
            console.error(
              "Verification error:",
              err
            );

            setError(
              err.message ||
                "Payment verification failed."
            );
          }
        },


        // -------------------------------------------------
        // User Closes Checkout
        // -------------------------------------------------

        modal: {
          ondismiss: function () {
            setPaymentMessage(
              "Payment window closed. No payment was confirmed."
            );
          },
        },


        // -------------------------------------------------
        // Razorpay UI
        // -------------------------------------------------

        theme: {
          color: "#6d5dfc",
        },
      };


      // ---------------------------------------------------
      // 5. Open Razorpay Checkout
      // ---------------------------------------------------

      const razorpay =
        new window.Razorpay(options);


      // ---------------------------------------------------
      // Payment Failure
      // ---------------------------------------------------

      razorpay.on(
        "payment.failed",
        function (response) {
          console.error(
            "Razorpay payment failed:",
            response.error
          );

          setError(
            response.error?.description ||
              "Payment failed. No purchase was completed."
          );
        }
      );

      razorpay.open();

    } catch (err) {
      console.error(
        "Payment error:",
        err
      );

      setError(
        err.message ||
          "Unable to start Razorpay payment."
      );

    } finally {
      setPaying(false);
    }
  };

// -------------------------------------------------------
// Load Live Agent Decision Receipt
// -------------------------------------------------------

const handleReceipt = async () => {
  if (!result?.transaction_id) {
    setError("Transaction ID is missing.");
    return;
  }

  setReceiptLoading(true);
  setError("");

  try {
    const response = await fetch(
      `${API_URL}/transactions/${result.transaction_id}/receipt`
    );

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(
        data.detail ||
        "Could not load the decision receipt."
      );
    }

    setLiveReceipt(data.receipt);

  } catch (err) {
    console.error(
      "Receipt error:",
      err
    );

    setError(
      err.message ||
      "Could not load the decision receipt."
    );

  } finally {
    setReceiptLoading(false);
  }
};
  // -------------------------------------------------------
  // Convenient Variables
  // -------------------------------------------------------

  const transaction =
    result?.transaction;

  const mission =
    result?.mission;

  const product =
    transaction?.selected_product;

  const policy =
    transaction?.policy_decision;

  const upsell =
    transaction?.upsell_decision;


  // -------------------------------------------------------
  // UI
  // -------------------------------------------------------

  return (
    <div className="app">
      <div className="container">

        <p className="eyebrow">
          AGENTIC COMMERCE
        </p>

        <h1>AegisCart</h1>

        <p className="tagline">
          The Trust Layer for Agentic Commerce
        </p>

        <p className="description">
          Tell your AI buyer what you need.
          AegisCart evaluates products,
          applies your spending rules,
          and prevents unauthorized purchases.
        </p>


        {/* Shopping Request */}

        <div className="request-card">

          <label htmlFor="shopping-request">
            What should your AI buyer find?
          </label>

          <textarea
            id="shopping-request"
            name="shopping-request"

            value={request}

            onChange={(event) =>
              setRequest(
                event.target.value
              )
            }

            placeholder="Find me a premium black abaya under ₹4000 within 2 days. Quality matters most."
          />

          <button
            onClick={handleCheckout}
            disabled={loading}
          >
            {loading
              ? "AI Buyer is thinking..."
              : "Start Agentic Checkout"}
          </button>

        </div>


        {/* Error */}

        {error && (
          <div className="error-message">

            <strong>
              AegisCart could not continue
            </strong>

            <p>
              {error}
            </p>

          </div>
        )}


        {/* Payment Message */}

        {paymentMessage && (
          <div className="approved-box">
            {paymentMessage}
          </div>
        )}


        {/* Successful Agent Decision */}

        {result?.success &&
          transaction && (

            <div className="result-card">

              <div className="result-heading">

                <div>

                  <p className="eyebrow">
                    AGENT DECISION
                  </p>

                  <h2>
                    {product?.name ||
                      "No matching product"}
                  </h2>

                </div>


                <span className="status-badge">
                  {transaction.status}
                </span>

              </div>
              
              {/* AI Interpretation Source */}
              
              {mission?.interpretation_source && ( <div
    className={`ai-source-box ${
      mission.interpretation_source === "GEMINI"
        ? "ai-source-live"
        : "ai-source-fallback"
    }`}
  >

    <div className="ai-source-icon">
      {mission.interpretation_source === "GEMINI"
        ? "✦"
        : "🛡️"}
    </div>

    <div>

      <strong>
        {mission.interpretation_source === "GEMINI"
          ? "Gemini Buyer Agent Active"
          : "Safe AI Fallback Active"}
      </strong>

      <p>
        {mission.interpretation_source === "GEMINI"
          ? "Your shopping request was interpreted by the Gemini buyer agent."
          : "The external AI service was unavailable, so AegisCart safely interpreted the request locally without bypassing any spending or payment rules."}
      </p>

    </div>

  </div>
)}

              {/* Product Details */}

              {product && (

                <div className="product-grid">

                  <div>

                    <span>
                      Price
                    </span>

                    <strong>
                      ₹{product.price}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Quality
                    </span>

                    <strong>
                      {product.quality}
                    </strong>

                  </div>


                  <div>

                    <span>
                      Delivery
                    </span>

                    <strong>
                      {product.delivery_days} days
                    </strong>

                  </div>


                  <div>

                    <span>
                      Agent score
                    </span>

                    <strong>
                      {product.score ?? "—"}
                    </strong>

                  </div>

                </div>
              )}


              {/* Merchant Upsell Protection */}

              {upsell && (

                <div className="upsell-box">

                  <div className="upsell-header">

                    <span className="shield-icon">
                      🛡️
                    </span>

                    <div>

                      <strong>
                        Merchant Upsell{" "}
                        {upsell.decision === "BLOCK"
                          ? "Blocked"
                          : "Evaluated"}
                      </strong>

                      <p>
                        AegisCart checked this
                        merchant offer against your
                        Purchase Constitution.
                      </p>

                    </div>

                  </div>


                  <div className="upsell-details">

                    <div>

                      <span>
                        Merchant suggested
                      </span>

                      <strong>
                        {upsell.name}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Upsell price
                      </span>

                      <strong>
                        ₹{upsell.price}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Purchase increase
                      </span>

                      <strong>
                        {typeof upsell.percentage ===
                        "number"
                          ? `${upsell.percentage.toFixed(
                              1
                            )}%`
                          : `${upsell.percentage}%`}
                      </strong>

                    </div>


                    <div>

                      <span>
                        Decision
                      </span>

                      <strong>
                        {upsell.decision}
                      </strong>

                    </div>

                  </div>


                  <p className="upsell-reason">
                    {upsell.reason}
                  </p>


                  {upsell.decision === "BLOCK" && (

                    <div className="upsell-protection-message">
                      ✓ This item was not added to
                      the Razorpay payment amount.
                    </div>

                  )}

                </div>
              )}


              {/* Purchase Constitution */}

              {policy && (

                <div className="policy-box">

                  <strong>
                    Purchase Constitution
                  </strong>

                  <p>
                    {policy.reason}
                  </p>

                </div>
              )}


              {/* Awaiting Approval */}

              {transaction.status ===
                "AWAITING_HUMAN_APPROVAL" &&
                product && (

                  <button
                    className="approval-button"

                    onClick={
                      handleApproval
                    }

                    disabled={
                      approving
                    }
                  >

                    {approving
                      ? "Approving..."
                      : `Approve ₹${product.price} Purchase`}

                  </button>
                )}


              {/* Ready for Payment */}

              {transaction.status ===
                "READY_FOR_PAYMENT" &&
                product && (

                  <>

                    <div className="approved-box">
                      ✓ Human approval recorded.
                      Transaction is ready for
                      secure payment.
                    </div>

                    <button
                      onClick={
                        handlePayment
                      }

                      disabled={
                        paying
                      }
                    >

                      {paying
                        ? "Preparing secure checkout..."
                        : `Pay ₹${product.price} with Razorpay`}

                    </button>

                  </>
                )}


              {/* Payment Pending */}

              {transaction.status ===
                "PAYMENT_PENDING" && (

                  <div className="policy-box">

                    <strong>
                      Payment Pending
                    </strong>

                    <p>
                      Razorpay order created.
                      Waiting for the payment
                      result.
                    </p>

                  </div>
                )}


              {/* Payment Verified */}

              {transaction.status ===
                "PAYMENT_VERIFIED" && (

                  <div className="approved-box">

                    ✓ Razorpay payment signature
                    verified by AegisCart.

                  </div>
                )}

                {/* Agent Decision Receipt Button */}

{transaction.status ===
  "PAYMENT_VERIFIED" && (

  <button
    className="receipt-button"
    onClick={handleReceipt}
    disabled={receiptLoading}
  >

    {receiptLoading
      ? "Building Decision Receipt..."
      : "View Agent Decision Receipt"}

  </button>
)}


{/* Live Agent Decision Receipt */}

{liveReceipt && (

  <div className="receipt-box">

    <div className="receipt-title">

      <p className="eyebrow">
        EXPLAINABLE COMMERCE
      </p>

      <h3>
        Agent Decision Receipt
      </h3>

      <span>
        {liveReceipt.transaction_status}
      </span>

    </div>


    <div className="receipt-summary">

      <div>
        <small>Merchant</small>

        <strong>
          {liveReceipt.merchant || "—"}
        </strong>
      </div>


      <div>
        <small>Selected Product</small>

        <strong>
          {liveReceipt.selected_product?.name || "—"}
        </strong>
      </div>


      <div>
        <small>Authorized Amount</small>

        <strong>
          ₹{liveReceipt.selected_product?.price || 0}
        </strong>
      </div>

    </div>


    <div className="timeline">

      {liveReceipt.decision_timeline?.map(
        (event, index) => (

          <div
            className="timeline-event"
            key={`${event.event}-${index}`}
          >

            <div className="timeline-marker">
              ✓
            </div>

            <div className="timeline-content">

              <strong>
                {event.event?.replaceAll(
                  "_",
                  " "
                )}
              </strong>

              <p>
                {event.message}
              </p>

            </div>

          </div>
        )
      )}

    </div>

  </div>
)}


              {/* No Matching Product */}

              {transaction.status ===
                "NO_MATCH" && (

                  <div className="policy-box">

                    <strong>
                      No safe match found
                    </strong>

                    <p>
                      {transaction.message ||
                        "No product satisfied all of your constraints."}
                    </p>

                  </div>
                )}

            </div>
          )}

      </div>
    </div>
  );
}

export default App;