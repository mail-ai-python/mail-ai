import React, { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import axios from "axios";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || "http://localhost:8008";

function Dashboard() {
  const [searchParams] = useSearchParams();
  const email = searchParams.get("email"); // Get logged-in user email
  
  const [isActive, setIsActive] = useState(false);
  const [logs, setLogs] = useState([]);
  const [refreshing, setRefreshing] = useState(false);

  // 1. Fetch Data on Load
  useEffect(() => {
    if (email) {
      fetchStatus();
      fetchLogs();
    }
  }, [email]);

  const fetchStatus = async () => {
    const res = await axios.post(`${BACKEND_URL}/api/check-user`, { email });
    setIsActive(res.data.is_active);
  };

  const fetchLogs = async () => {
    setRefreshing(true);
    const res = await axios.get(`${BACKEND_URL}/api/logs/${email}`);
    setLogs(res.data);
    setRefreshing(false);
  };

  const toggleStatus = async () => {
    const res = await axios.post(`${BACKEND_URL}/api/user/${email}/toggle`);
    setIsActive(res.data.is_active);
  };

  if (!email) return <div className="app-container"><h1>Please Login First</h1></div>;

  return (
    <div className="app-container" style={{ alignItems: 'flex-start', paddingTop: '50px' }}>
      <div className="login-card" style={{ width: "800px", maxWidth: "90%" }}>
        
        {/* HEADER SECTION */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px' }}>
          <div style={{ textAlign: 'left' }}>
            <h2>👋 Welcome, {email.split('@')[0]}</h2>
            <p style={{ margin: 0, color: isActive ? 'green' : 'gray' }}>
              ● System is {isActive ? "LISTENING" : "PAUSED"}
            </p>
          </div>
          
          <button 
            onClick={toggleStatus}
            style={{
              padding: "10px 25px",
              borderRadius: "30px",
              border: "none",
              color: "white",
              fontWeight: "bold",
              cursor: "pointer",
              backgroundColor: isActive ? "#d32f2f" : "#2e7d32"
            }}
          >
            {isActive ? "🛑 STOP AGENT" : "▶ START AGENT"}
          </button>
        </div>

        {/* LOGS SECTION */}
        <div style={{ textAlign: 'left' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
            <h3>Recent Activity</h3>
            <button onClick={fetchLogs} disabled={refreshing} style={{ background: 'none', border: 'none', color: '#4285F4', cursor: 'pointer' }}>
              {refreshing ? "Refreshing..." : "↻ Refresh"}
            </button>
          </div>

          <div style={{ maxHeight: "400px", overflowY: "auto", border: "1px solid #eee", borderRadius: "8px" }}>
            {logs.length === 0 ? (
              <div style={{ padding: "20px", textAlign: "center", color: "#999" }}>No emails processed yet.</div>
            ) : (
              logs.map((log) => (
                <div key={log._id} style={{ padding: "15px", borderBottom: "1px solid #f0f0f0" }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: "0.85rem", color: "#666" }}>
                    <span><strong>From:</strong> {log.sender}</span>
                    <span>{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                  <div style={{ fontWeight: "bold", margin: "5px 0" }}>{log.subject}</div>
                  <div style={{ background: "#f9f9f9", padding: "10px", borderRadius: "5px", fontSize: "0.9rem", color: "#333" }}>
                    {log.summary}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>
    </div>
  );
}

export default Dashboard;