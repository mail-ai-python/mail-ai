import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8008";

function Login() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleContinue = async (e) => {
    e.preventDefault();
    if (!email) return;

    setLoading(true);
    try {
      // 1. Ask Backend: Is this user registered?
      const checkRes = await axios.post(`${BACKEND_URL}/api/check-user`, { email });
      
      if (checkRes.data.exists) {
        // CASE A: EXISTING USER -> Go straight to Dashboard
        navigate(`/dashboard?email=${email}`);
      } else {
        // CASE B: NEW USER -> Go to Google OAuth
        const authRes = await axios.get(`${BACKEND_URL}/login?email_hint=${email}`);
        if (authRes.data.auth_url) {
          window.location.href = authRes.data.auth_url;
        }
      }
    } catch (err) {
      console.error(err);
      alert("Connection Error");
    }
    setLoading(false);
  };

  return (
    <div className="app-container">
      <div className="login-card">
        <h1>📧 Mail AI Agent</h1>
        <p>Enter your email to continue</p>
        
        <form onSubmit={handleContinue}>
          <input
            type="email"
            placeholder="name@gmail.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={styles.input}
            required
          />
          
          <button type="submit" className="google-btn" disabled={loading} style={{marginTop: '15px'}}>
            {loading ? "Checking..." : "Continue"}
          </button>
        </form>
      </div>
    </div>
  );
}

const styles = {
  input: {
    width: "90%",
    padding: "12px",
    borderRadius: "5px",
    border: "1px solid #ddd",
    fontSize: "16px"
  }
};

export default Login;