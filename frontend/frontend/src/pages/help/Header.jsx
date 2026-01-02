import React from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft } from "lucide-react";

export default function HelpHeader({ title = "Help", subtitle = "" }) {
  const navigate = useNavigate();
  return (
    <div className="container" style={{ padding: "1rem 0" }}>
      <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
        <button
          onClick={() => navigate(-1)}
          aria-label="Go back"
          style={{
            background: "none",
            border: "none",
            cursor: "pointer",
            padding: 6,
            display: "inline-flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <ArrowLeft />
        </button>

        <div>
          <h1 style={{ margin: 0, fontSize: "1.5rem", fontWeight: 700, color: "#0f172a" }}>{title}</h1>
          {subtitle && (
            <p style={{ margin: 0, marginTop: "0.25rem", color: "#64748b", fontSize: "0.95rem" }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
