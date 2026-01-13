import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import "./App.css"; // Reuse existing styles

function Success() {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState("");

  useEffect(() => {
    // Read query params from URL (e.g., ?email=abc@gmail.com&status=Active)
    setEmail(searchParams.get("email") || "Unknown User");
    setStatus(searchParams.get("status") || "Unknown Status");
  }, [searchParams]);

  return (
    <div className="app-container">
      <div className="login-card" style={{ borderColor: "#0f9d58", borderTop: "5px solid #0f9d58" }}>
        <h1 style={{ color: "#0f9d58" }}>✅ Success!</h1>
        <p>Onboarding is complete.</p>
        
        <div style={{ textAlign: "left", background: "#f8f9fa", padding: "15px", borderRadius: "5px", fontSize: "0.9rem" }}>
          <p style={{ margin: "5px 0" }}><strong>User:</strong> {email}</p>
          <p style={{ margin: "5px 0" }}><strong>Watch Status:</strong> {status}</p>
        </div>
        <button 
          onClick={() => window.location.href = `/dashboard?email=${email}`}
          style={{ marginTop: "20px", padding: "10px 20px", background: "#4285F4", color: "white", border: "none", borderRadius: "5px", cursor: "pointer" }}
        >
          Go to Dashboard
        </button>
        {/* <p style={{ marginTop: "20px", fontSize: "0.8rem", color: "#666" }}>
          You can now close this tab.
        </p> */}
      </div>
    </div>
  );
}

export default Success;