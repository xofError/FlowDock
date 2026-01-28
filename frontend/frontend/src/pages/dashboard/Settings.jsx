import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { X, Link } from "lucide-react";
import TopNavBar from "../../layout/TopNavBar";
import { useAuth } from "../../hooks/useAuth";
import api from "../../services/api";
import { QRCodeSVG } from "qrcode.react";
import DashboardIcon from "../../resources/icons/dashboard.svg";
import MyFilesIcon from "../../resources/icons/my_files.svg";
import SharedIcon from "../../resources/icons/shared.svg";
import TrashIcon from "../../resources/icons/trash.svg";
import SettingsIcon from "../../resources/icons/settings.svg";
import SecurityIcon from "../../resources/icons/security.svg";
import KeyIcon from "../../resources/icons/key_24dp_000000_FILL0_wght400_GRAD0_opsz24.svg";

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: null, label: "Public Links", to: "/public-links", lucideIcon: "Link" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

const settingsNavItems = [
  { id: "account", label: "Account" },
  { id: "security", label: "Security" },
  { id: "storage", label: "Storage" },
  { id: "sessions", label: "Sessions" },
];

export default function Settings() {
  const routerNavigate = useNavigate();
  const { user, refreshUser } = useAuth();
  const [activeSection, setActiveSection] = useState("account");
  const [profileName, setProfileName] = useState("");
  const [profileEmail, setProfileEmail] = useState("");
  const [tempName, setTempName] = useState("");
  const [tempEmail, setTempEmail] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [passwordForm, setPasswordForm] = useState({ current: "", new: "", confirm: "" });
  const [twoFAData, setTwoFAData] = useState(null);
  const [twoFACode, setTwoFACode] = useState("");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [sessions, setSessions] = useState([]);
  const [showEmptyTrashConfirm, setShowEmptyTrashConfirm] = useState(false);
  const accountRef = useRef(null);
  const securityRef = useRef(null);
  const storageRef = useRef(null);
  const sessionsRef = useRef(null);

  useEffect(() => {
    if (user) {
      setProfileName(user.full_name || "");
      setProfileEmail(user.email || "");
      setTempName(user.full_name || "");
      setTempEmail(user.email || "");
    }
  }, [user]);

  useEffect(() => {
    function onToggle() { setMobileSidebarOpen(s => !s); }
    window.addEventListener("toggleMobileSidebar", onToggle);
    return () => window.removeEventListener("toggleMobileSidebar", onToggle);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileSidebarOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileSidebarOpen]);

  // Load sessions when component mounts
  useEffect(() => {
    const loadSessions = async () => {
      try {
        const sessionsData = await api.getSessions();
        setSessions(sessionsData);
      } catch (err) {
        console.error("Failed to load sessions:", err);
      }
    };
    loadSessions();
  }, []);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleUpdateProfile = async (e) => {
    e?.preventDefault?.();
    setErrorMessage("");
    
    if (!tempName.trim()) {
      setErrorMessage("Name is required");
      return;
    }

    setLoading(true);
    try {
      const response = await api.updateProfile({ full_name: tempName });
      // Update both display name and temp name
      setProfileName(tempName);
      setTempName(tempName);
      // Refresh user data from backend to ensure consistency
      await refreshUser();
      setSuccessMessage("✓ Profile updated successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (e) => {
    e.preventDefault();
    setErrorMessage("");

    if (!passwordForm.current || !passwordForm.new || !passwordForm.confirm) {
      setErrorMessage("All fields are required");
      return;
    }

    if (passwordForm.new !== passwordForm.confirm) {
      setErrorMessage("New passwords don't match");
      return;
    }

    if (passwordForm.new.length < 8) {
      setErrorMessage("Password must be at least 8 characters");
      return;
    }

    setLoading(true);
    try {
      await api.changePassword(passwordForm.current, passwordForm.new);
      setPasswordForm({ current: "", new: "", confirm: "" });
      setSuccessMessage("✓ Password changed successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Failed to change password");
    } finally {
      setLoading(false);
    }
  };

  const start2FASetup = async () => {
    setErrorMessage("");
    setLoading(true);
    try {
      const data = await api.setup2FA();
      setTwoFAData(data);
    } catch (err) {
      setErrorMessage(err.message || "Could not start 2FA setup");
    } finally {
      setLoading(false);
    }
  };

  const confirm2FA = async () => {
    setErrorMessage("");
    if (!twoFACode || twoFACode.length !== 6) {
      setErrorMessage("Please enter a valid 6-digit code");
      return;
    }

    setLoading(true);
    try {
      await api.enable2FA(twoFACode);
      setTwoFAData(null);
      setTwoFACode("");
      await refreshUser();
      setSuccessMessage("✓ 2FA Enabled Successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Invalid Code");
    } finally {
      setLoading(false);
    }
  };

  const handleDisable2FA = async () => {
    const password = prompt("Enter your password to disable 2FA:");
    if (!password) return;

    setErrorMessage("");
    setLoading(true);
    try {
      await api.disable2FA(password);
      await refreshUser();
      setSuccessMessage("✓ 2FA Disabled Successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Failed to disable 2FA");
    } finally {
      setLoading(false);
    }
  };

  const handleEmptyTrash = async () => {
    setErrorMessage("");
    setLoading(true);
    try {
      await api.emptyTrash(user.id);
      setSuccessMessage("✓ Trash emptied successfully!");
      setShowEmptyTrashConfirm(false);
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Failed to empty trash");
    } finally {
      setLoading(false);
    }
  };

  const confirmEmptyTrash = () => {
    setShowEmptyTrashConfirm(true);
  };

  const handleRevokeSession = async (sessionId) => {
    if (!window.confirm("Are you sure you want to logout from this session?")) {
      return;
    }

    setErrorMessage("");
    setLoading(true);
    try {
      await api.revokeSession(sessionId);
      // Reload sessions
      const sessionsData = await api.getSessions();
      setSessions(sessionsData);
      setSuccessMessage("✓ Session revoked successfully!");
      setTimeout(() => setSuccessMessage(""), 3000);
    } catch (err) {
      setErrorMessage(err.message || "Failed to revoke session");
    } finally {
      setLoading(false);
    }
  };

  const handleRevokeAllSessions = async () => {
    if (!window.confirm("Are you sure you want to logout from all devices? You will be logged out immediately.")) {
      return;
    }

    setErrorMessage("");
    setLoading(true);
    try {
      await api.revokeAllSessions();
      // Logout user
      await api.logout();
      routerNavigate("/login");
    } catch (err) {
      setErrorMessage(err.message || "Failed to revoke all sessions");
      setLoading(false);
    }
  };

  const scrollToSection = (sectionId) => {
    setActiveSection(sectionId);
    setTimeout(() => {
      if (sectionId === "account" && accountRef.current) {
        accountRef.current.scrollIntoView({ behavior: "smooth" });
      } else if (sectionId === "security" && securityRef.current) {
        securityRef.current.scrollIntoView({ behavior: "smooth" });
      } else if (sectionId === "storage" && storageRef.current) {
        storageRef.current.scrollIntoView({ behavior: "smooth" });
      } else if (sectionId === "sessions" && sessionsRef.current) {
        sessionsRef.current.scrollIntoView({ behavior: "smooth" });
      }
    }, 100);
  };

  return (
    <TopNavBar>
      <style>{`
        .sidebar-btn {
          display: flex;
          align-items: center;
          justify-content: flex-start;
          width: 100%;
          gap: 0.3cm;
          height: 2rem;
          font-size: 0.875rem;
          padding: 0.5rem 0.8rem;
          border-radius: 0.5rem;
          outline: none;
          border: none;
          background-color: transparent;
          color: #64748b;
          font-weight: 400;
          transition: all 0.2s ease;
          cursor: pointer;
          margin-bottom: 0.6rem;
        }
        .sidebar-btn:hover { background-color: #f1f5f9; }
        .sidebar-btn.active { background-color: #e2e8f0; color: #0f172a; font-weight: 500; }

        .settings-nav-btn {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          border: none;
          background: transparent;
          cursor: pointer;
          font-size: 0.875rem;
          color: #64748b;
          transition: all 0.2s;
          border-bottom: 2px solid transparent;
        }
        .settings-nav-btn:hover { color: #0f172a; }
        .settings-nav-btn.active { color: #2563eb; border-bottom: 2px solid #2563eb; }

        .input-field {
          width: 100%;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          padding: 0.75rem;
          font-size: 0.875rem;
          margin-bottom: 1rem;
        }
        .input-field:focus { outline: none; border-color: #2563eb; box-shadow: 0 0 0 3px rgba(37,99,235,0.1); }

        .update-btn { background-color: #2563eb; color: #fff; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight:500; font-size:0.875rem; transition: background-color 0.2s; }
        .update-btn:hover:not(:disabled) { background-color: #1d4ed8; }
        .update-btn:disabled { opacity: 0.5; cursor: not-allowed; }
        .secondary-btn { background-color: #e5e7eb; color: #000; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: 500; font-size:0.875rem; transition: background-color 0.2s; }
        .secondary-btn:hover:not(:disabled) { background-color: #d1d5db; }
        .secondary-btn:disabled { opacity: 0.5; cursor: not-allowed; }

        .success-message { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; padding: 0.75rem; border-radius: 6px; margin-top: 1rem; font-size: 0.875rem; }
        .error-message { background-color: #fee2e2; color: #991b1b; border: 1px solid #fecaca; padding: 0.75rem; border-radius: 6px; margin-top: 1rem; font-size: 0.875rem; }

        .mobile-menu { position: fixed; inset:0; background-color: rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:center; z-index:60; }
        .panel { background:#ffffff; border-radius:8px; padding:1.5rem; max-width:400px; width:90%; box-shadow:0 10px 40px rgba(0,0,0,0.15); }
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
          {navItems.map((item, idx) => (
            <button
              key={idx}
              className={`sidebar-btn ${idx === 5 ? "active" : ""}`}
              onClick={() => routerNavigate(item.to)}
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
        </nav>
      </aside>

      {/* Main Content */}
      <main 
        style={{ 
          flex: 1, 
          paddingLeft: "3rem", 
          paddingRight: "3rem", 
          paddingTop: "2.5rem", 
          paddingBottom: "2.5rem", 
          overflowY: "auto", 
          backgroundColor: "#ffffff" 
        }}
      >
        <header style={{ marginBottom: "2rem" }}>
          <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>
            Settings
          </h1>

          {/* Settings Sub-Navigation */}
          <div style={{ display: "flex", gap: "2rem", borderBottom: "1px solid #e5e7eb", marginBottom: "2rem" }}>
            {settingsNavItems.map((item) => (
              <button
                key={item.id}
                className={`settings-nav-btn ${activeSection === item.id ? "active" : ""}`}
                onClick={() => scrollToSection(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
        </header>

        {/* Messages */}
        {successMessage && <div className="success-message" style={{ marginBottom: "1rem" }}>{successMessage}</div>}
        {errorMessage && <div className="error-message" style={{ marginBottom: "1rem" }}>{errorMessage}</div>}

        {/* Account Section */}
        <section ref={accountRef} style={{ marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>
            Account
          </h2>

          <div style={{ maxWidth: "500px" }}>
            <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.875rem", fontWeight: "500", color: "#374151" }}>
              Name
            </label>
            <input
              type="text"
              value={tempName}
              onChange={(e) => {
                setTempName(e.target.value);
                if (errorMessage) setErrorMessage("");
              }}
              className="input-field"
              style={{ marginBottom: "1.5rem" }}
            />

            <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.875rem", fontWeight: "500", color: "#374151" }}>
              Email
            </label>
            <input
              type="email"
              value={profileEmail}
              disabled
              className="input-field"
              style={{ marginBottom: "2rem", backgroundColor: "#f3f4f6", cursor: "not-allowed" }}
            />
            <p style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: "1.5rem" }}>Email cannot be changed directly.</p>

            <button className="update-btn" onClick={handleUpdateProfile} disabled={loading} style={{ marginRight: "1rem" }}>
              {loading ? "Saving..." : "Update Profile"}
            </button>
          </div>

          {/* Storage Section */}
          <div ref={storageRef} style={{ marginTop: "2rem", maxWidth: "500px" }}>
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>Storage</h3>
            <div style={{ padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px", marginBottom: "1.5rem" }}>
              <div style={{ marginBottom: "1rem" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.5rem", fontSize: "0.875rem", color: "#374151" }}>
                  <span>Used Storage</span>
                  <span style={{ fontWeight: "600" }}>
                    {user ? `${(user.storage_used / 1024 / 1024).toFixed(2)} MB / ${(user.storage_limit / 1024 / 1024 / 1024).toFixed(1)} GB` : "Loading..."}
                  </span>
                </div>
                <div style={{ width: "100%", height: "8px", backgroundColor: "#e5e7eb", borderRadius: "4px", overflow: "hidden" }}>
                  <div style={{ 
                    width: user ? `${(user.storage_used / user.storage_limit) * 100}%` : "0%", 
                    height: "100%", 
                    backgroundColor: "#2563eb", 
                    transition: "width 0.3s ease" 
                  }}></div>
                </div>
              </div>
            </div>
            <button className="secondary-btn" onClick={confirmEmptyTrash} disabled={loading} style={{ backgroundColor: "#fee2e2", color: "#991b1b" }}>
              {loading ? "Emptying..." : "Empty Trash"}
            </button>
          </div>
        </section>

        {/* Security Section */}
        <section ref={securityRef} style={{ marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>
            Security
          </h2>

          <div style={{ maxWidth: "500px" }}>
            {/* Password Change */}
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>
              Change Password
            </h3>
            <div style={{ marginBottom: "2rem", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px" }}>
              <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.875rem", fontWeight: "500", color: "#374151" }}>
                Current Password
              </label>
              <input
                type="password"
                value={passwordForm.current}
                onChange={(e) => setPasswordForm({ ...passwordForm, current: e.target.value })}
                className="input-field"
              />

              <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.875rem", fontWeight: "500", color: "#374151" }}>
                New Password
              </label>
              <input
                type="password"
                value={passwordForm.new}
                onChange={(e) => setPasswordForm({ ...passwordForm, new: e.target.value })}
                className="input-field"
              />

              <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.875rem", fontWeight: "500", color: "#374151" }}>
                Confirm New Password
              </label>
              <input
                type="password"
                value={passwordForm.confirm}
                onChange={(e) => setPasswordForm({ ...passwordForm, confirm: e.target.value })}
                className="input-field"
                style={{ marginBottom: "1rem" }}
              />

              <button className="update-btn" onClick={handlePasswordChange} disabled={loading} style={{ marginRight: "1rem" }}>
                {loading ? "Updating..." : "Update Password"}
              </button>
            </div>

            {/* Two-Factor Authentication */}
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>
              Two-Factor Authentication
            </h3>
            <div style={{ padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px", marginBottom: "2rem" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                  <img src={KeyIcon} alt="Security" style={{ width: "1.25rem", height: "1.25rem" }} />
                  <span style={{ fontSize: "0.875rem", color: "#64748b" }}>
                    Protect your account with an extra layer of security using an authenticator app.
                  </span>
                </div>
                <span style={{ paddingLeft: "1rem", paddingRight: "0.75rem", paddingTop: "0.25rem", paddingBottom: "0.25rem", borderRadius: "9999px", fontSize: "0.75rem", fontWeight: "600", backgroundColor: user?.is_2fa_enabled ? "#dbeafe" : "#f3f4f6", color: user?.is_2fa_enabled ? "#0369a1" : "#6b7280" }}>
                  {user?.is_2fa_enabled ? "ENABLED" : "DISABLED"}
                </span>
              </div>

              {!user?.is_2fa_enabled && !twoFAData && (
                <button className="update-btn" onClick={start2FASetup} disabled={loading}>
                  {loading ? "Loading..." : "Enable 2FA"}
                </button>
              )}

              {twoFAData && (
                <div style={{ backgroundColor: "#eff6ff", padding: "1rem", borderRadius: "6px", marginTop: "1rem" }}>
                  <h4 style={{ fontSize: "0.875rem", fontWeight: "600", color: "#1e40af", marginBottom: "1rem" }}>
                    Setup Authenticator App
                  </h4>
                  <div style={{ display: "flex", flexDirection: "row", alignItems: "center", gap: "1.5rem", marginBottom: "1rem" }}>
                    <div style={{ backgroundColor: "#ffffff", padding: "0.5rem", borderRadius: "6px" }}>
                      {twoFAData.otpauth_url && <QRCodeSVG value={twoFAData.otpauth_url} size={120} />}
                    </div>
                    <div>
                      <p style={{ fontSize: "0.875rem", color: "#1e40af", marginBottom: "1rem" }}>
                        1. Scan this QR code with Google Authenticator or Authy.<br/>
                        2. Enter the 6-digit code below to confirm.
                      </p>
                      <div style={{ display: "flex", gap: "0.5rem" }}>
                        <input
                          type="text"
                          placeholder="000000"
                          maxLength={6}
                          value={twoFACode}
                          onChange={(e) => setTwoFACode(e.target.value.replace(/\D/g,''))}
                          style={{ width: "6rem", textAlign: "center", fontFamily: "monospace", fontSize: "1.125rem", letterSpacing: "0.1em" }}
                          className="input-field"
                        />
                        <button className="update-btn" onClick={confirm2FA} disabled={loading} style={{ margin: 0 }}>
                          {loading ? "Verifying..." : "Verify"}
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {user?.is_2fa_enabled && !twoFAData && (
                <button className="secondary-btn" onClick={handleDisable2FA} disabled={loading} style={{ backgroundColor: "#fee2e2", color: "#991b1b" }}>
                  {loading ? "Disabling..." : "Disable 2FA"}
                </button>
              )}
            </div>
          </div>
        </section>

        {/* Sessions Section */}
        <section ref={sessionsRef} style={{ marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>
            Sessions & Devices
          </h2>

          <div style={{ maxWidth: "600px" }}>
            <p style={{ fontSize: "0.875rem", color: "#64748b", marginBottom: "1.5rem" }}>
              Manage your active sessions and devices. You can logout from specific devices or all devices at once.
            </p>

            {sessions && sessions.length > 0 ? (
              <div style={{ marginBottom: "2rem" }}>
                {sessions.map((session) => (
                  <div key={session.id} style={{ padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px", marginBottom: "1rem", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: "600", color: "#0f172a", marginBottom: "0.5rem", fontSize: "0.875rem" }}>
                        {session.browser_name || "Unknown Browser"}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: "0.25rem" }}>
                        IP: {session.ip_address || "Unknown"}
                      </div>
                      <div style={{ fontSize: "0.75rem", color: "#64748b" }}>
                        Last Active: {session.created_at ? new Date(session.created_at).toLocaleDateString() : "Unknown"}
                      </div>
                      {session.active === false && (
                        <div style={{ fontSize: "0.75rem", color: "#991b1b", marginTop: "0.25rem", fontWeight: "500" }}>
                          INACTIVE
                        </div>
                      )}
                    </div>
                    {session.active !== false && (
                      <button 
                        className="secondary-btn" 
                        onClick={() => handleRevokeSession(session.id)}
                        disabled={loading}
                        style={{ backgroundColor: "#fee2e2", color: "#991b1b", marginLeft: "1rem" }}
                      >
                        {loading ? "..." : "Logout"}
                      </button>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px", textAlign: "center", color: "#64748b", marginBottom: "2rem" }}>
                No active sessions found
              </div>
            )}

            <button 
              className="secondary-btn" 
              onClick={handleRevokeAllSessions}
              disabled={loading}
              style={{ backgroundColor: "#fee2e2", color: "#991b1b" }}
            >
              {loading ? "Logging Out..." : "Logout From All Devices"}
            </button>
          </div>
        </section>
      </main>

      {/* Mobile sidebar panel */}
      {mobileSidebarOpen && (
        <div className="mobile-menu" onClick={() => setMobileSidebarOpen(false)} style={{ zIndex: 60 }}>
          <div className="panel" onClick={(e) => e.stopPropagation()}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
              <strong>FlowDock</strong>
              <button onClick={() => setMobileSidebarOpen(false)} style={{ background: "none", border: "none", cursor: "pointer" }}>✕</button>
            </div>
            <nav style={{ display: "flex", flexDirection: "column", gap: "0.6rem" }}>
              {navItems.map((item, idx) => (
                <button key={idx} onClick={() => { setMobileSidebarOpen(false); routerNavigate(item.to); }} style={{ display: "flex", gap: "0.5rem", alignItems: "center", padding: "0.6rem 0.2rem", background: "transparent", border: "none", cursor: "pointer" }}>
                  {item.lucideIcon === "Link" ? (
                    <Link style={{ width: "1rem", height: "1rem", color: "#64748b" }} />
                  ) : (
                    <img src={item.icon} alt="" style={{ width: "1rem", height: "1rem" }} />
                  )}
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Empty Trash Confirmation Modal */}
      {showEmptyTrashConfirm && (
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
          zIndex: 1000,
        }}>
          <div style={{
            backgroundColor: "white",
            borderRadius: "12px",
            padding: "2rem",
            maxWidth: "400px",
            width: "90%",
            boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
          }}>
            <h3 style={{ fontSize: "1.25rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1rem" }}>
              Empty Trash?
            </h3>
            <p style={{ color: "#64748b", marginBottom: "1.5rem", lineHeight: "1.5" }}>
              Are you sure you want to permanently delete all files in trash? This action cannot be undone.
            </p>
            <div style={{ display: "flex", gap: "1rem", justifyContent: "flex-end" }}>
              <button
                onClick={() => setShowEmptyTrashConfirm(false)}
                disabled={loading}
                style={{
                  padding: "0.5rem 1.5rem",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                  backgroundColor: "white",
                  color: "#64748b",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: "500",
                  opacity: loading ? 0.6 : 1,
                }}>
                Cancel
              </button>
              <button
                onClick={handleEmptyTrash}
                disabled={loading}
                style={{
                  padding: "0.5rem 1.5rem",
                  border: "none",
                  borderRadius: "8px",
                  backgroundColor: "#dc2626",
                  color: "white",
                  cursor: loading ? "not-allowed" : "pointer",
                  fontWeight: "500",
                  opacity: loading ? 0.6 : 1,
                }}>
                {loading ? "Emptying..." : "Delete Permanently"}
              </button>
            </div>
          </div>
        </div>
      )}
    </TopNavBar>
  );
}
