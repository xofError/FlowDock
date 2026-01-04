import React, { useState, useEffect } from "react";
import { Copy, Trash2, Calendar, Download, Link } from "lucide-react";
import { useNavigate as useRouterNavigate } from "react-router-dom";
import TopNavBar from "../../layout/TopNavBar";
import DashboardIcon from "../../resources/icons/dashboard.svg";
import MyFilesIcon from "../../resources/icons/my_files.svg";
import SharedIcon from "../../resources/icons/shared.svg";
import TrashIcon from "../../resources/icons/trash.svg";
import SettingsIcon from "../../resources/icons/settings.svg";
import { api } from "../../services/api";
import { useAuth } from "../../hooks/useAuth";

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: null, label: "Public Links", to: "/public-links", lucideIcon: "Link" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

export default function PublicLinks() {
  const routerNavigate = useRouterNavigate();
  const { user } = useAuth();
  const [links, setLinks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [expandedLink, setExpandedLink] = useState(null);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [extendModal, setExtendModal] = useState(null);
  const [extendDays, setExtendDays] = useState("30");
  const [limitModal, setLimitModal] = useState(null);
  const [limitValue, setLimitValue] = useState("0");

  useEffect(() => {
    if (user?.id) {
      fetchPublicLinks();
    }
  }, [user?.id]);

  const fetchPublicLinks = async () => {
    if (!user?.id) return;
    try {
      setLoading(true);
      const publicLinks = await api.getUserPublicLinks(user.id);
      // Filter out inactive (deleted) links
      const activeLinks = (publicLinks || []).filter(link => link.active !== false);
      setLinks(activeLinks);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch public links:", err);
      setError("Failed to load public links");
    } finally {
      setLoading(false);
    }
  };

  const handleCopyLink = (token) => {
    const linkUrl = `${window.location.origin}/#/s/${token}/access`;
    navigator.clipboard.writeText(linkUrl);
    setSuccessMessage("Link copied to clipboard!");
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  const handleDeleteLink = async (linkId) => {
    try {
      await api.deletePublicLink(linkId);
      // Remove the deleted link from the list
      setLinks(links.filter(link => link.id !== linkId));
      setSuccessMessage("✓ Link deleted successfully");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      console.error("Failed to delete link:", err);
      setError("Failed to delete link");
    }
  };

  const handleExtendExpiry = async (linkId) => {
    setExtendModal(linkId);
    setExtendDays("30");
  };

  const confirmExtendExpiry = async () => {
    if (!extendModal) return;
    const days = parseInt(extendDays);
    if (isNaN(days) || days <= 0) {
      setError("Please enter a valid number of days");
      return;
    }

    try {
      const currentDate = new Date();
      const newExpiry = new Date(currentDate.getTime() + days * 24 * 60 * 60 * 1000);
      
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      const updated = await api.request(
        `${mediaApiUrl}/share-links/${extendModal}/extend-expiry?new_expiry=${encodeURIComponent(newExpiry.toISOString())}`,
        { method: "PATCH" }
      );

      // Update the link in the list
      setLinks(links.map(link => 
        link.id === extendModal 
          ? { ...link, expires_at: updated.expires_at }
          : link
      ));
      setSuccessMessage("✓ Expiry date extended");
      setExtendModal(null);
      setExtendDays("30");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      console.error("Failed to extend expiry:", err);
      setError("Failed to extend expiry date");
    }
  };

  const handleUpdateDownloadLimit = async (linkId) => {
    setLimitModal(linkId);
    setLimitValue("0");
  };

  const confirmUpdateDownloadLimit = async () => {
    if (!limitModal) return;
    const limit = parseInt(limitValue);
    if (isNaN(limit) || limit < 0) {
      setError("Please enter a valid number (0 or greater)");
      return;
    }

    try {
      const mediaApiUrl = import.meta.env.VITE_MEDIA_API_URL || "http://localhost:8001/media";
      const updated = await api.request(
        `${mediaApiUrl}/share-links/${limitModal}/update-download-limit?max_downloads=${limit}`,
        { method: "PATCH" }
      );

      // Update the link in the list
      setLinks(links.map(link => 
        link.id === limitModal 
          ? { ...link, max_downloads: updated.max_downloads }
          : link
      ));
      setSuccessMessage("✓ Download limit updated");
      setLimitModal(null);
      setLimitValue("0");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      console.error("Failed to update download limit:", err);
      setError("Failed to update download limit");
    }
  };

  const formatFileSize = (bytes) => {
    if (!bytes || bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <>
      <TopNavBar>
        <style>{`
          .sidebar-btn { display:flex; align-items:center; justify-content:flex-start; width:100%; gap:0.3cm; height:2rem; font-size:0.875rem; padding:0.5rem 0.8rem; border-radius:0.5rem; outline:none; border:none; background-color:transparent; color:#64748b; font-weight:400; transition:all .2s ease; cursor:pointer; margin-bottom:0.6rem; }
          .sidebar-btn:hover { background-color:#f1f5f9; }
          .sidebar-btn.active { background-color:#e2e8f0; color:#0f172a; font-weight:500; }
          .mobile-menu { position:fixed; inset:0; background:rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:flex-end; z-index:60; }
          .panel { background:#fff; border-radius:8px; padding:1.5rem; width:320px; max-width:85%; box-shadow:-8px 0 24px rgba(0,0,0,0.12); }
          .content-width { width:90%; max-width:90%; margin-left:0; }
          .success-message { padding:1rem; background:#dcfce7; color:#166534; border:1px solid #bbf7d0; border-radius:6px; margin-bottom:1.5rem; text-align:center; font-size:0.875rem; }
          .error-message { padding:1rem; background:#fee2e2; color:#991b1b; border:1px solid #fecaca; border-radius:6px; margin-bottom:1.5rem; text-align:center; font-size:0.875rem; }
          .link-card { padding:1.25rem; border:1px solid #e5e7eb; border-radius:8px; margin-bottom:1rem; background:#ffffff; transition:all 0.2s; }
          .link-card:hover { box-shadow:0 4px 12px rgba(0,0,0,0.1); }
          .link-url { font-family:monospace; font-size:0.875rem; color:#0f172a; word-break:break-all; padding:0.5rem; background:#f3f4f6; border-radius:4px; margin:0.75rem 0; }
          .link-meta { display:flex; justify-content:space-between; font-size:0.75rem; color:#64748b; margin-top:0.75rem; }
          .link-actions { display:flex; gap:0.5rem; margin-top:1rem; flex-wrap:wrap; }
          .link-btn { padding:0.5rem 0.75rem; border:none; border-radius:4px; cursor:pointer; font-size:0.75rem; font-weight:500; transition:all 0.2s; display:flex; align-items:center; gap:0.25rem; }
          .link-btn.primary { background:#2563eb; color:white; }
          .link-btn.primary:hover { background:#1d4ed8; }
          .link-btn.secondary { background:#e5e7eb; color:#0f172a; }
          .link-btn.secondary:hover { background:#d1d5db; }
          .link-btn.danger { background:#fee2e2; color:#dc2626; }
          .link-btn.danger:hover { background:#fecaca; }
          .link-status { display:inline-block; padding:0.25rem 0.5rem; border-radius:4px; font-size:0.7rem; font-weight:500; }
          .link-status.active { background:#dcfce7; color:#166534; }
          .link-status.expired { background:#fee2e2; color:#dc2626; }
        `}</style>

        {/* Sidebar */}
        <aside className="sidebar-responsive"
          style={{ 
            width: "calc(100vw * 5 / 17 * 0.75 * 0.85)",
            backgroundColor: "#ffffff",
            paddingLeft: "1cm",
            paddingRight: "1.5rem",
            paddingTop: "1.5rem",
            paddingBottom: "1.5rem",
            display: "flex",
            flexDirection: "column",
            flexShrink: 0,
          }}
        >
          <nav style={{ flex: 1 }}>
            {navItems.map((item, idx) => {
              const isActive = window.location.hash === `#${item.to}`;
              return (
                <button
                  key={idx}
                  className={`sidebar-btn ${isActive ? "active" : ""}`}
                  onClick={() => routerNavigate(item.to)}
                >
                  {item.lucideIcon === "Link" ? (
                    <Link style={{ width: "1.1rem", height: "1.1rem", flexShrink: 0, color: isActive ? "#0f172a" : "#64748b", transition: "color 0.2s ease" }} />
                  ) : (
                    <img 
                      src={item.icon} 
                      alt="" 
                      style={{ width: "1.1rem", height: "1.1rem", flexShrink: 0 }} 
                    />
                  )}
                  <span style={{ fontSize: "0.875rem" }}>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Extend Expiry Modal */}
        {extendModal && (
          <div style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
          onClick={() => setExtendModal(null)}
          >
            <div style={{
              backgroundColor: "white",
              padding: "2rem",
              borderRadius: "8px",
              maxWidth: "400px",
              width: "90%",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
            }}
            onClick={(e) => e.stopPropagation()}
            >
              <h2 style={{ marginTop: 0, marginBottom: "1rem", color: "#0f172a", fontSize: "1.25rem", fontWeight: 600 }}>Extend Expiry Date</h2>
              <div style={{ marginBottom: "1.5rem" }}>
                <label style={{ display: "block", marginBottom: "0.5rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Days to extend</label>
                <input
                  type="number"
                  min="1"
                  value={extendDays}
                  onChange={(e) => setExtendDays(e.target.value)}
                  style={{
                    width: "100%",
                    border: "1px solid #d1d5db",
                    borderRadius: "6px",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.875rem",
                    boxSizing: "border-box"
                  }}
                />
              </div>
              <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
                <button
                  onClick={() => setExtendModal(null)}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: "#e5e7eb",
                    color: "#0f172a",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                    fontWeight: 500
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={confirmExtendExpiry}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: "#2563eb",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                    fontWeight: 500
                  }}
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Update Download Limit Modal */}
        {limitModal && (
          <div style={{
            position: "fixed",
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            backgroundColor: "rgba(0, 0, 0, 0.5)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 1000
          }}
          onClick={() => setLimitModal(null)}
          >
            <div style={{
              backgroundColor: "white",
              padding: "2rem",
              borderRadius: "8px",
              maxWidth: "400px",
              width: "90%",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
            }}
            onClick={(e) => e.stopPropagation()}
            >
              <h2 style={{ marginTop: 0, marginBottom: "1rem", color: "#0f172a", fontSize: "1.25rem", fontWeight: 600 }}>Update Download Limit</h2>
              <div style={{ marginBottom: "1.5rem" }}>
                <label style={{ display: "block", marginBottom: "0.5rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Maximum downloads (0 = unlimited)</label>
                <input
                  type="number"
                  min="0"
                  value={limitValue}
                  onChange={(e) => setLimitValue(e.target.value)}
                  style={{
                    width: "100%",
                    border: "1px solid #d1d5db",
                    borderRadius: "6px",
                    padding: "0.5rem 0.75rem",
                    fontSize: "0.875rem",
                    boxSizing: "border-box"
                  }}
                />
              </div>
              <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
                <button
                  onClick={() => setLimitModal(null)}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: "#e5e7eb",
                    color: "#0f172a",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                    fontWeight: 500
                  }}
                >
                  Cancel
                </button>
                <button
                  onClick={confirmUpdateDownloadLimit}
                  style={{
                    padding: "0.75rem 1.5rem",
                    backgroundColor: "#2563eb",
                    color: "white",
                    border: "none",
                    borderRadius: "6px",
                    cursor: "pointer",
                    fontSize: "0.875rem",
                    fontWeight: 500
                  }}
                >
                  Confirm
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Main Content */}
        <main style={{ padding: "2rem", flex: 1, overflowY: "auto" }}>
          <header style={{ marginBottom: "2rem" }}>
            <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "#0f172a" }}>Public Links</h1>
            <p style={{ fontSize: "0.875rem", color: "#64748b", marginTop: "0.5rem" }}>
              Manage all public sharing links you've created
            </p>
          </header>

          {/* Success Message */}
          {successMessage && (
            <div className="success-message">{successMessage}</div>
          )}

          {/* Error Message */}
          {error && (
            <div className="error-message">{error}</div>
          )}

          {/* Loading State */}
          {loading && (
            <div style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
              <p>Loading your public links...</p>
            </div>
          )}

          {/* Empty State */}
          {!loading && links.length === 0 && (
            <div style={{
              backgroundColor: "#f9fafb",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              padding: "2rem",
              textAlign: "center"
            }}>
              <p style={{ color: "#64748b", marginBottom: "1rem" }}>
                You haven't created any public links yet.
              </p>
              <p style={{ fontSize: "0.875rem", color: "#9ca3af" }}>
                Create public links from your files or folders to share them without needing a user account.
              </p>
            </div>
          )}

          {/* Links List */}
          {!loading && links.length > 0 && (
            <div className="content-width">
              {links.map((link) => {
                const isExpired = link.expires_at && new Date(link.expires_at) < new Date();
                const isLimitReached = link.max_downloads > 0 && link.downloads_used >= link.max_downloads;
                const isActive = !isExpired && !isLimitReached && link.active;

                return (
                  <div key={link.id} className="link-card">
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "0.75rem" }}>
                      <div style={{ flex: 1 }}>
                        <p style={{ fontSize: "0.875rem", color: "#0f172a", fontWeight: 500, margin: "0 0 0.25rem 0" }}>
                          File: {link.file_id.substring(0, 12)}...
                        </p>
                      </div>
                      <span className={`link-status ${isActive ? "active" : "expired"}`}>
                        {isActive ? "Active" : isExpired ? "Expired" : "Limit reached"}
                      </span>
                    </div>

                    <div className="link-url">
                      {`${window.location.origin}/#/s/${link.short_code}/access`}
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.75rem", fontSize: "0.75rem", color: "#64748b" }}>
                      <div>
                        <p style={{ margin: 0, fontWeight: 500 }}>Created</p>
                        <p style={{ margin: "0.25rem 0 0 0" }}>
                          {new Date(link.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div>
                        <p style={{ margin: 0, fontWeight: 500 }}>Expires</p>
                        <p style={{ margin: "0.25rem 0 0 0" }}>
                          {link.expires_at ? new Date(link.expires_at).toLocaleDateString() : "Never"}
                        </p>
                      </div>
                      <div>
                        <p style={{ margin: 0, fontWeight: 500 }}>Downloads</p>
                        <p style={{ margin: "0.25rem 0 0 0" }}>
                          {link.max_downloads > 0 ? `${link.downloads_used}/${link.max_downloads}` : "Unlimited"}
                        </p>
                      </div>
                      <div>
                        <p style={{ margin: 0, fontWeight: 500 }}>Password</p>
                        <p style={{ margin: "0.25rem 0 0 0" }}>
                          {link.has_password ? "Protected" : "Public"}
                        </p>
                      </div>
                    </div>

                    <div className="link-actions">
                      <button
                        className="link-btn primary"
                        onClick={() => handleCopyLink(link.short_code)}
                      >
                        <Copy size={14} />
                        Copy
                      </button>
                      <button
                        className="link-btn secondary"
                        onClick={() => handleExtendExpiry(link.id)}
                        disabled={isExpired}
                        style={{ opacity: isExpired ? 0.5 : 1 }}
                      >
                        <Calendar size={14} />
                        Extend
                      </button>
                      <button
                        className="link-btn secondary"
                        onClick={() => handleUpdateDownloadLimit(link.id)}
                      >
                        <Download size={14} />
                        Limit
                      </button>
                      <button
                        className="link-btn danger"
                        onClick={() => handleDeleteLink(link.id)}
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </main>

        {/* Mobile Sidebar */}
        {mobileSidebarOpen && (
          <div className="mobile-menu" onClick={() => setMobileSidebarOpen(false)}>
            <div className="panel" onClick={(e) => e.stopPropagation()}>
              {navItems.map((item, idx) => (
                <button
                  key={idx}
                  className={`sidebar-btn ${idx === 3 ? "active" : ""}`}
                  onClick={() => {
                    routerNavigate(item.to);
                    setMobileSidebarOpen(false);
                  }}
                >
                  {item.lucideIcon === "Link" ? (
                    <Link style={{ width: "1.1rem", height: "1.1rem", flexShrink: 0, color: "#64748b" }} />
                  ) : (
                    <img 
                      src={item.icon} 
                      alt="" 
                      style={{ width: "1.1rem", height: "1.1rem", flexShrink: 0 }} 
                    />
                  )}
                  <span style={{ fontSize: "0.875rem" }}>{item.label}</span>
                </button>
              ))}
            </div>
          </div>
        )}
      </TopNavBar>

      <style>{`
        body { margin: 0; padding: 0; }
      `}</style>
    </>
  );
}
