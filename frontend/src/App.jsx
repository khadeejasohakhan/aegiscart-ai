import { useState } from "react";
import "./App.css";

function App() {
  const [request, setRequest] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleCheckout = async () => {
    if (!request.trim()) return;

    setLoading(true);
    setResult(null);

    try {
      const response = await fetch("http://127.0.0.1:8000/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          user_request: request,
        }),
      });

      const data = await response.json();
      setResult(data);
    } catch (error) {
      setResult({
        success: false,
        error: "Could not connect to AegisCart backend.",
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <div className="container">
        <p className="eyebrow">AGENTIC COMMERCE</p>

        <h1>AegisCart</h1>

        <p className="tagline">
          The Trust Layer for Agentic Commerce
        </p>

        <p className="description">
          Tell your AI buyer what you need. AegisCart evaluates products,
          applies your spending rules, and prevents unauthorized purchases.
        </p>

        <div className="request-card">
          <label>What should your AI buyer find?</label>

          <textarea
            value={request}
            onChange={(event) => setRequest(event.target.value)}
            placeholder="Find me a premium black abaya under ₹4000 within 2 days. Quality matters most."
          />

          <button onClick={handleCheckout} disabled={loading}>
            {loading ? "AI Buyer is thinking..." : "Start Agentic Checkout"}
          </button>
        </div>

        {result && (
          <div className="result-card">
            <h2>Agent Decision</h2>

            {result.success ? (
              <>
                <p>
                  <strong>Status:</strong>{" "}
                  {result.transaction?.status}
                </p>

                <p>
                  <strong>Selected:</strong>{" "}
                  {result.transaction?.selected_product?.name || "No match"}
                </p>

                {result.transaction?.selected_product && (
                  <>
                    <p>
                      <strong>Price:</strong> ₹
                      {result.transaction.selected_product.price}
                    </p>

                    <p>
                      <strong>Quality:</strong>{" "}
                      {result.transaction.selected_product.quality}
                    </p>
                  </>
                )}

                {result.transaction?.policy_decision && (
                  <p>
                    <strong>Policy:</strong>{" "}
                    {result.transaction.policy_decision.reason}
                  </p>
                )}
              </>
            ) : (
              <p>Request failed. Please try again.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;