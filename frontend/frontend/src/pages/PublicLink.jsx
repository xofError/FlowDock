import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Header from "../layout/Header";
import DocumentIcon from "../resources/icons/document.svg";
import { api } from "../services/api";

export default function PublicLink() {
  const { token } = useParams();
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [password, setPassword] = useState("");
  const [needsPassword, setNeedsPassword] = useState(false);

  useEffect(() => {
    fetchFileMetadata();
  }, [token]);

  const fetchFileMetadata = async () => {
    try {
      setLoading(true);
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      const url = `${mediaApiUrl}/s/${token}/metadata${password ? `?password=${encodeURIComponent(password)}` : ""}`;
      console.log("Fetching file metadata from:", url);
      const response = await fetch(url);
      console.log("Response status:", response.status);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.log("Error response:", errorData);
        // Check for password required response
        if (response.status === 403 || response.status === 401 || errorData.detail?.includes("Password")) {
          console.log("Password required detected");
          setNeedsPassword(true);
          setError(null);
          setLoading(false);
          return;
        }
        throw new Error(`HTTP ${response.status}`);
      }
      
      const data = await response.json();
      console.log("File metadata retrieved:", data);
      setFile(data);
      setError(null);
      setNeedsPassword(false);
    } catch (err) {
      console.error("Failed to fetch file metadata:", err);
      if (err.message && err.message.includes("404")) {
        setError("Share link not found or has expired.");
      } else if (err.message && err.message.includes("410")) {
        setError("This share link has expired or download limit has been exceeded.");
      } else {
        setError("Failed to access this file. Please check the link.");
      }
      setNeedsPassword(false);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    try {
      setDownloading(true);
      
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      
      // Step 1: Request access via the /s/{token}/access endpoint
      const accessResponse = await fetch(`${mediaApiUrl}/s/${token}/access`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          password: password || null,
        }),
      });

      if (!accessResponse.ok) {
        if (accessResponse.status === 403) {
          setNeedsPassword(true);
          setError("Invalid password. Please try again.");
        } else if (accessResponse.status === 410) {
          setError("This link has expired or download limit exceeded.");
        } else {
          setError("Failed to access share link.");
        }
        return;
      }

      const accessData = await accessResponse.json();
      const downloadUrl = accessData.download_url;

      // Step 2: Download the file using the download URL
      const downloadResponse = await fetch(downloadUrl);

      if (!downloadResponse.ok) {
        if (downloadResponse.status === 410) {
          setError("This link has expired or download limit exceeded.");
        } else {
          setError("Failed to download file.");
        }
        return;
      }

      // Get the filename from Content-Disposition header or use the file name
      const contentDisposition = downloadResponse.headers.get("content-disposition");
      const filename = file?.name || "download";
      
      // Convert response to blob
      const blob = await downloadResponse.blob();

      // Create object URL and trigger download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      // Refresh metadata to update download count
      fetchFileMetadata();
    } catch (err) {
      console.error("Download failed:", err);
      setError("Failed to download file. Please try again.");
    } finally {
      setDownloading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    if (!password.trim()) {
      setError("Please enter a password");
      return;
    }
    console.log("Password submitted, retrying metadata fetch with password");
    setError(null);
    fetchFileMetadata();
  };

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
        <Header />
        <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
          <div style={{ textAlign: "center" }}>
            <p style={{ color: "#64748b" }}>Loading file information...</p>
          </div>
        </main>
      </div>
    );
  }

  if (error && !needsPassword) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
        <Header />
        <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
          <div style={{ textAlign: "center", maxWidth: "500px" }}>
            <h1 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1rem" }}>
              Access Denied
            </h1>
            <p style={{ color: "#64748b", marginBottom: "2rem" }}>{error}</p>
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
              }}
            >
              Go Home
            </button>
          </div>
        </main>
      </div>
    );
  }

  // Password form for password-protected links
  if (needsPassword) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
        <Header />
        <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
          <div style={{ maxWidth: "400px", width: "100%" }}>
            <div style={{
              backgroundColor: "#ffffff",
              padding: "2rem",
              borderRadius: "12px",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
              border: "1px solid #e5e7eb"
            }}>
              <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1rem", marginTop: 0 }}>
                Password Required
              </h2>
              <p style={{ color: "#64748b", marginBottom: "1.5rem", fontSize: "0.875rem" }}>
                This file is password protected. Please enter the password to access it.
              </p>
              
              {error && (
                <div style={{
                  padding: "0.75rem",
                  backgroundColor: "#fee2e2",
                  color: "#991b1b",
                  borderRadius: "6px",
                  marginBottom: "1rem",
                  fontSize: "0.875rem",
                  border: "1px solid #fecaca"
                }}>
                  {error}
                </div>
              )}

              <form onSubmit={handlePasswordSubmit}>
                <div style={{ marginBottom: "1.5rem" }}>
                  <label style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    color: "#374151",
                    fontSize: "0.875rem",
                    fontWeight: 500
                  }}>
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      setError(null);
                    }}
                    placeholder="Enter password"
                    autoFocus
                    style={{
                      width: "100%",
                      padding: "0.75rem",
                      border: "1px solid #d1d5db",
                      borderRadius: "6px",
                      fontSize: "1rem",
                      boxSizing: "border-box",
                      outline: "none",
                      transition: "border-color 0.2s"
                    }}
                    onFocus={(e) => e.target.style.borderColor = "#2563eb"}
                    onBlur={(e) => e.target.style.borderColor = "#d1d5db"}
                  />
                </div>

                <button
                  type="submit"
                  style={{
                    width: "100%",
                    padding: "0.75rem",
                    backgroundColor: "#2563eb",
                    color: "#ffffff",
                    border: "none",
                    borderRadius: "6px",
                    fontSize: "1rem",
                    fontWeight: 600,
                    cursor: "pointer",
                    transition: "background-color 0.2s"
                  }}
                  onMouseEnter={(e) => e.target.style.backgroundColor = "#1d4ed8"}
                  onMouseLeave={(e) => e.target.style.backgroundColor = "#2563eb"}
                >
                  Unlock File
                </button>
              </form>

              <button
                onClick={() => navigate("/")}
                style={{
                  width: "100%",
                  marginTop: "1rem",
                  padding: "0.75rem",
                  backgroundColor: "#f3f4f6",
                  color: "#374151",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  fontSize: "0.875rem",
                  fontWeight: 500,
                  cursor: "pointer",
                  transition: "background-color 0.2s"
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = "#e5e7eb"}
                onMouseLeave={(e) => e.target.style.backgroundColor = "#f3f4f6"}
              >
                Go Home
              </button>
            </div>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
      <Header />

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
            {file?.name || "Unknown File"}
          </h2>

          {/* File Info */}
          <div style={{ marginBottom: "2rem" }}>
            <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "0.5rem" }}>
              File size: {formatFileSize(file?.size)}
            </p>
            {file?.expires_at && (
              <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "0.5rem" }}>
                Expires: {new Date(file.expires_at).toLocaleDateString()}
              </p>
            )}
            {file?.max_downloads > 0 && (
              <p style={{ fontSize: "0.875rem", color: "#64748b" }}>
                Downloads: {file.downloads_used}/{file.max_downloads}
              </p>
            )}
          </div>

          {/* Password Input (if needed) */}
          {needsPassword && (
            <div style={{ marginBottom: "2rem" }}>
              <input
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={(e) => e.key === "Enter" && handleDownload()}
                style={{
                  width: "100%",
                  padding: "0.75rem",
                  border: "1px solid #d1d5db",
                  borderRadius: "8px",
                  fontSize: "1rem",
                  marginBottom: "1rem",
                  boxSizing: "border-box",
                }}
              />
              {error && (
                <p style={{ fontSize: "0.875rem", color: "#dc2626", marginBottom: "1rem" }}>
                  {error}
                </p>
              )}
            </div>
          )}

          {/* Download Button */}
          <button
            onClick={handleDownload}
            disabled={downloading}
            style={{
              backgroundColor: downloading ? "#d1d5db" : "#2563eb",
              color: "#ffffff",
              border: "none",
              padding: "0.75rem 2rem",
              borderRadius: "8px",
              fontSize: "1rem",
              fontWeight: "600",
              cursor: downloading ? "not-allowed" : "pointer",
              transition: "background-color 0.2s",
            }}
            onMouseEnter={(e) => !downloading && (e.target.style.backgroundColor = "#1d4ed8")}
            onMouseLeave={(e) => !downloading && (e.target.style.backgroundColor = "#2563eb")}
          >
            {downloading ? "Downloading..." : "Download"}
          </button>
        </div>
      </main>
    </div>
  );
}
