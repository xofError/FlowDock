import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { ChevronRight, Download, ArrowLeft, Folder, File } from "lucide-react";
import Header from "../layout/Header";
import { api } from "../services/api";

export default function PublicFolderBrowser() {
  const { token, folderId } = useParams();
  const navigate = useNavigate();
  const [currentFolder, setCurrentFolder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [password, setPassword] = useState("");
  const [needsPassword, setNeedsPassword] = useState(false);
  const [breadcrumbs, setBreadcrumbs] = useState([]);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    fetchFolderContents();
  }, [token, folderId]);

  const fetchFolderContents = async () => {
    try {
      setLoading(true);
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      
      // If folderId is provided, navigate to that subfolder, otherwise use root
      const endpoint = folderId 
        ? `${mediaApiUrl}/public/folders/${token}/subfolder/${folderId}/contents`
        : `${mediaApiUrl}/public/folders/${token}/contents`;
      
      const url = new URL(endpoint);
      if (password) {
        url.searchParams.append("password", password);
      }
      
      const response = await fetch(url.toString());
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        
        if (response.status === 403 || errorData.detail?.includes("Password")) {
          setNeedsPassword(true);
          setError(null);
          setLoading(false);
          return;
        }
        
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }
      
      const data = await response.json();
      setCurrentFolder(data);
      setNeedsPassword(false);
      // Keep password in state for downloads - don't clear it!
      setError(null);
      
      // Build breadcrumbs
      buildBreadcrumbs(data);
    } catch (err) {
      console.error("Failed to fetch folder contents:", err);
      setError(err.message || "Failed to load folder contents");
      setNeedsPassword(false);
    } finally {
      setLoading(false);
    }
  };

  const buildBreadcrumbs = (folderData) => {
    const crumbs = [
      { name: "Root", id: null }
    ];
    
    // Add parent folders if available
    if (folderData.breadcrumbs) {
      folderData.breadcrumbs.forEach(crumb => {
        crumbs.push({ name: crumb.name, id: crumb.folder_id });
      });
    }
    
    // Add current folder
    crumbs.push({ name: folderData.folder.name, id: folderData.folder.folder_id });
    
    setBreadcrumbs(crumbs);
  };

  const handleNavigateToFolder = (subfolderId) => {
    navigate(`/public/folders/${token}/browse/${subfolderId}`);
  };

  const handleNavigateToBreadcrumb = (breadcrumbId) => {
    if (breadcrumbId === null) {
      // Navigate to root
      navigate(`/public/folders/${token}`);
    } else {
      navigate(`/public/folders/${token}/browse/${breadcrumbId}`);
    }
  };

  const handleDownloadFile = async (fileId, fileName) => {
    try {
      setDownloading(true);
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      
      // Request file download via public link
      const response = await fetch(
        `${mediaApiUrl}/public/folders/${token}/download-file/${fileId}${password ? `?password=${encodeURIComponent(password)}` : ""}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) {
        if (response.status === 403) {
          setNeedsPassword(true);
          setError("Invalid password. Please try again.");
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
        return;
      }

      // Download the file
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      setError("Failed to download file");
    } finally {
      setDownloading(false);
    }
  };

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (!password.trim()) {
      setError("Please enter a password");
      return;
    }
    setError(null);
    fetchFolderContents();
  };

  const handleDownloadFolder = async () => {
    try {
      setDownloading(true);
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      
      const response = await fetch(
        `${mediaApiUrl}/public/folders/${token}/download-zip${password ? `?password=${encodeURIComponent(password)}` : ""}`,
        {
          method: "GET",
        }
      );

      if (!response.ok) {
        if (response.status === 403) {
          setNeedsPassword(true);
          setError("Invalid password. Please try again.");
        } else {
          throw new Error(`HTTP ${response.status}`);
        }
        return;
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${currentFolder.folder.name}.zip`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      setError("Failed to download folder");
    } finally {
      setDownloading(false);
    }
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
            <p style={{ color: "#64748b" }}>Loading folder contents...</p>
          </div>
        </main>
      </div>
    );
  }

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
                This folder is password protected. Please enter the password to access it.
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
                  Unlock Folder
                </button>
              </form>
            </div>
          </div>
        </main>
      </div>
    );
  }

  if (error) {
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

  if (!currentFolder) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#ffffff" }}>
        <Header />
        <main style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", padding: "2rem" }}>
          <div style={{ textAlign: "center" }}>
            <p style={{ color: "#64748b" }}>Folder not found</p>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column", backgroundColor: "#f9fafb" }}>
      <Header />

      <main style={{ flex: 1, padding: "2rem" }}>
        <div style={{ maxWidth: "1000px", margin: "0 auto" }}>
          {/* Header */}
          <div style={{ marginBottom: "2rem" }}>
            <button
              onClick={() => navigate(-1)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                backgroundColor: "transparent",
                border: "1px solid #d1d5db",
                color: "#0f172a",
                padding: "0.5rem 1rem",
                borderRadius: "6px",
                cursor: "pointer",
                marginBottom: "1rem",
                fontSize: "0.875rem",
                fontWeight: 500,
              }}
            >
              <ArrowLeft size={16} />
              Back
            </button>

            <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "#0f172a", marginBottom: "0.5rem", margin: "0" }}>
              📁 {currentFolder.folder.name}
            </h1>

            {/* Breadcrumbs */}
            <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginTop: "1rem", flexWrap: "wrap" }}>
              {breadcrumbs.map((crumb, idx) => (
                <React.Fragment key={idx}>
                  <button
                    onClick={() => handleNavigateToBreadcrumb(crumb.id)}
                    style={{
                      backgroundColor: "transparent",
                      border: "none",
                      color: crumb.id === currentFolder.folder.folder_id ? "#0f172a" : "#2563eb",
                      cursor: "pointer",
                      fontSize: "0.875rem",
                      textDecoration: crumb.id === currentFolder.folder.folder_id ? "none" : "underline",
                      fontWeight: crumb.id === currentFolder.folder.folder_id ? 500 : 400,
                    }}
                  >
                    {crumb.name}
                  </button>
                  {idx < breadcrumbs.length - 1 && (
                    <ChevronRight size={14} style={{ color: "#64748b" }} />
                  )}
                </React.Fragment>
              ))}
            </div>
          </div>

          {/* Download Folder Button */}
          <button
            onClick={handleDownloadFolder}
            disabled={downloading}
            style={{
              display: "flex",
              alignItems: "center",
              gap: "0.5rem",
              backgroundColor: downloading ? "#d1d5db" : "#2563eb",
              color: "#ffffff",
              border: "none",
              padding: "0.75rem 1.5rem",
              borderRadius: "8px",
              fontSize: "0.875rem",
              fontWeight: 600,
              cursor: downloading ? "not-allowed" : "pointer",
              marginBottom: "2rem",
            }}
          >
            <Download size={16} />
            {downloading ? "Downloading..." : "Download Folder"}
          </button>

          {/* Contents */}
          {(!currentFolder.files?.length && !currentFolder.subfolders?.length) ? (
            <div style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "2rem",
              textAlign: "center"
            }}>
              <p style={{ color: "#64748b" }}>This folder is empty</p>
            </div>
          ) : (
            <div style={{
              backgroundColor: "#ffffff",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              overflow: "hidden"
            }}>
              {/* Subfolders */}
              {currentFolder.subfolders && currentFolder.subfolders.length > 0 && (
                <div>
                  <div style={{
                    padding: "1rem",
                    backgroundColor: "#f9fafb",
                    borderBottom: "1px solid #e5e7eb",
                    fontWeight: 600,
                    color: "#0f172a",
                    fontSize: "0.875rem"
                  }}>
                    Folders ({currentFolder.subfolders.length})
                  </div>
                  {currentFolder.subfolders.map((subfolder) => (
                    <div
                      key={subfolder.folder_id}
                      onClick={() => handleNavigateToFolder(subfolder.folder_id)}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "1rem",
                        padding: "1rem",
                        borderBottom: "1px solid #e5e7eb",
                        cursor: "pointer",
                        transition: "background-color 0.2s",
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#f3f4f6"}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}
                    >
                      <Folder size={20} style={{ color: "#f59e0b" }} />
                      <div style={{ flex: 1 }}>
                        <p style={{ margin: 0, color: "#0f172a", fontSize: "0.875rem", fontWeight: 500 }}>
                          {subfolder.name}
                        </p>
                        <p style={{ margin: "0.25rem 0 0 0", color: "#64748b", fontSize: "0.75rem" }}>
                          Created: {new Date(subfolder.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <ChevronRight size={16} style={{ color: "#64748b" }} />
                    </div>
                  ))}
                </div>
              )}

              {/* Files */}
              {currentFolder.files && currentFolder.files.length > 0 && (
                <div>
                  <div style={{
                    padding: "1rem",
                    backgroundColor: "#f9fafb",
                    borderTop: currentFolder.subfolders?.length > 0 ? "1px solid #e5e7eb" : "none",
                    borderBottom: "1px solid #e5e7eb",
                    fontWeight: 600,
                    color: "#0f172a",
                    fontSize: "0.875rem"
                  }}>
                    Files ({currentFolder.files.length})
                  </div>
                  {currentFolder.files.map((file) => (
                    <div
                      key={file.file_id}
                      style={{
                        display: "flex",
                        alignItems: "center",
                        gap: "1rem",
                        padding: "1rem",
                        borderBottom: "1px solid #e5e7eb",
                        transition: "background-color 0.2s",
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.backgroundColor = "#f3f4f6"}
                      onMouseLeave={(e) => e.currentTarget.style.backgroundColor = "transparent"}
                    >
                      <File size={20} style={{ color: "#6366f1" }} />
                      <div style={{ flex: 1 }}>
                        <p style={{ margin: 0, color: "#0f172a", fontSize: "0.875rem", fontWeight: 500 }}>
                          {file.name}
                        </p>
                        <p style={{ margin: "0.25rem 0 0 0", color: "#64748b", fontSize: "0.75rem" }}>
                          {formatFileSize(file.size)} • {new Date(file.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDownloadFile(file.file_id, file.name)}
                        disabled={downloading}
                        style={{
                          backgroundColor: downloading ? "#d1d5db" : "#2563eb",
                          color: "#ffffff",
                          border: "none",
                          padding: "0.5rem 1rem",
                          borderRadius: "6px",
                          cursor: downloading ? "not-allowed" : "pointer",
                          fontSize: "0.75rem",
                          fontWeight: 500,
                        }}
                      >
                        Download
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
