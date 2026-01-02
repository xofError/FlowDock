import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import Header from "../layout/Header";
import DocumentIcon from "../resources/icons/document.svg";

export default function PublicLink() {
  const { linkId } = useParams();
  const navigate = useNavigate();

  // Mock file data - in real app, fetch from backend using linkId
  const sharedFile = {
    id: 1,
    name: "Document 1",
    size: "2.5 MB",
    type: "PDF",
    downloadUrl: "/api/download/shared/" + linkId,
  };

  const handleDownload = () => {
    // Trigger download
    const link = document.createElement("a");
    link.href = sharedFile.downloadUrl;
    link.download = sharedFile.name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
      {/* Header */}
      <Header />

      {/* Main Content */}
      <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
        <div style={{ textAlign: "center", maxWidth: "500px" }}>
          {/* Title */}
          <h1 style={{ fontSize: "2.25rem", fontWeight: "bold", color: "#0f172a", marginBottom: "2rem" }}>
            Shared File
          </h1>

          {/* Document Icon */}
          <div
            style={{
              width: "100px",
              height: "100px",
              backgroundColor: "#f3f4f6",
              borderRadius: "12px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              margin: "0 auto 1.5rem",
            }}
          >
            <img
              src={DocumentIcon}
              alt="Document"
              style={{ width: "60px", height: "60px" }}
            />
          </div>

          {/* File Name */}
          <h2 style={{ fontSize: "1.5rem", fontWeight: "600", color: "#0f172a", marginBottom: "0.75rem" }}>
            {sharedFile.name}
          </h2>

          {/* File Size */}
          <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "2rem" }}>
            File size: {sharedFile.size}
          </p>

          {/* Download Button */}
          <button
            onClick={handleDownload}
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
            }}
            onMouseEnter={(e) => (e.target.style.backgroundColor = "#1d4ed8")}
            onMouseLeave={(e) => (e.target.style.backgroundColor = "#2563eb")}
          >
            Download
          </button>
        </div>
      </main>
    </div>
  );
}
