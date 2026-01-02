import React from "react";
import { useNavigate } from "react-router-dom";
import MainLayout from "../layout/MainLayout";

export default function NotFound() {
  const navigate = useNavigate();

  return (
    <MainLayout hideSidebar={true}>
      <div className="min-h-screen flex items-center justify-center px-4">
        <div style={{ textAlign: "center", maxWidth: "500px" }}>
          {/* 404 Text */}
          <h1 style={{
            fontSize: "5rem",
            fontWeight: "900",
            color: "#0f172a",
            margin: 0,
            lineHeight: "1"
          }}>
            404
          </h1>

          {/* Main Heading */}
          <h2 style={{
            fontSize: "2rem",
            fontWeight: "700",
            color: "#0f172a",
            marginTop: "1rem",
            marginBottom: "1rem"
          }}>
            Oops! Page Not Found
          </h2>

          {/* Description */}
          <p style={{
            fontSize: "1rem",
            color: "#64748b",
            marginBottom: "2rem",
            lineHeight: "1.6"
          }}>
            The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
          </p>

          {/* Go to Home Button */}
          <button
            onClick={() => navigate("/")}
            style={{
              backgroundColor: "#2563eb",
              color: "#ffffff",
              border: "none",
              padding: "0.75rem 2rem",
              borderRadius: "8px",
              fontSize: "1rem",
              fontWeight: "600",
              cursor: "pointer",
              transition: "background-color 0.2s",
              marginBottom: "1.5rem",
              display: "inline-block"
            }}
            onMouseEnter={(e) => (e.target.style.backgroundColor = "#1d4ed8")}
            onMouseLeave={(e) => (e.target.style.backgroundColor = "#2563eb")}
          >
            Go to Home
          </button>

          {/* Support Text */}
          <p style={{
            fontSize: "0.75rem",
            color: "#64748b",
            marginTop: "1rem"
          }}>
            If you believe this is an error, please contact support at{" "}
            <a
              href="mailto:support@flowdock.com"
              style={{
                color: "#2563eb",
                textDecoration: "underline",
                cursor: "pointer"
              }}
            >
              support@flowdock.com
            </a>
          </p>
        </div>
      </div>
    </MainLayout>
  );
}
