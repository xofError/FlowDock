import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { X } from "lucide-react";
import TopNavBar from "../../layout/TopNavBar";
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
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

const settingsNavItems = [
  { id: "account", label: "Account" },
  { id: "storage", label: "Storage" },
  { id: "security", label: "Security" },
];

const SAMPLE_DEVICES = [
  { id: 1, name: "Chrome on MacOS", date: "Currently using" },
  { id: 2, name: "Safari on MacOS", date: "May 15, 2025" },
];

const RECOVERY_PHRASE = "aurora bridge crystal delta echo forest gamma horizon india jungle keeper";

export default function Settings() {
  const routerNavigate = useNavigate();
  const [activeSection, setActiveSection] = useState("account");
  const [profileName, setProfileName] = useState("");
  const [profileEmail, setProfileEmail] = useState("");
  const [tempName, setTempName] = useState(profileName);
  const [tempEmail, setTempEmail] = useState(profileEmail);
  const [successMessage, setSuccessMessage] = useState("");
  const [emailError, setEmailError] = useState("");
  const [emptyTrashWarning, setEmptyTrashWarning] = useState(false);
  const [enable2FA, setEnable2FA] = useState(false);
  const [recoveryPhraseModal, setRecoveryPhraseModal] = useState(false);
  const [devices, setDevices] = useState(SAMPLE_DEVICES);
  const [deviceToRemove, setDeviceToRemove] = useState(null);
  const [removeDeviceWarning, setRemoveDeviceWarning] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const accountRef = useRef(null);
  const storageRef = useRef(null);
  const securityRef = useRef(null);

  useEffect(() => {
    function onToggle() { setMobileSidebarOpen(s => !s); }
    window.addEventListener("toggleMobileSidebar", onToggle);
    return () => window.removeEventListener("toggleMobileSidebar", onToggle);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileSidebarOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileSidebarOpen]);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleUpdateProfile = () => {
    setEmailError("");
    
    if (!tempName.trim()) {
      setEmailError("Name is required");
      return;
    }

    if (!tempEmail.trim()) {
      setEmailError("Email is required");
      return;
    }

    if (!validateEmail(tempEmail)) {
      setEmailError("Please enter a valid email address (e.g., user@example.com)");
      return;
    }

    setProfileName(tempName);
    setProfileEmail(tempEmail);
    setSuccessMessage(`✓ Profile updated successfully! Name: ${tempName}, Email: ${tempEmail}`);
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  const handleEmptyTrash = () => {
    setEmptyTrashWarning(true);
  };

  const confirmEmptyTrash = () => {
    setEmptyTrashWarning(false);
    setSuccessMessage("✓ Trash emptied successfully! All files have been permanently deleted.");
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  const handleRemoveDevice = (deviceId) => {
    setDeviceToRemove(deviceId);
    setRemoveDeviceWarning(true);
  };

  const confirmRemoveDevice = () => {
    if (deviceToRemove) {
      setDevices(prev => prev.filter(d => d.id !== deviceToRemove));
      setRemoveDeviceWarning(false);
      setSuccessMessage("✓ Device removed and logged out successfully.");
      setTimeout(() => setSuccessMessage(""), 3000);
    }
  };

  const handleLogoutAllDevices = () => {
    setDevices([]);
    setSuccessMessage("✓ Logged out from all devices successfully.");
    setTimeout(() => setSuccessMessage(""), 3000);
  };

  const handleRegenerateRecovery = () => {
    setRecoveryPhraseModal(true);
  };

  const scrollToSection = (sectionId) => {
    setActiveSection(sectionId);
    setTimeout(() => {
      if (sectionId === "account" && accountRef.current) {
        accountRef.current.scrollIntoView({ behavior: "smooth" });
      } else if (sectionId === "storage" && storageRef.current) {
        storageRef.current.scrollIntoView({ behavior: "smooth" });
      } else if (sectionId === "security" && securityRef.current) {
        securityRef.current.scrollIntoView({ behavior: "smooth" });
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
        .update-btn:hover { background-color: #1d4ed8; }
        .empty-btn, .secondary-btn { background-color: #e5e7eb; color: #000; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; font-weight: 500; font-size:0.875rem; transition: background-color 0.2s; }
        .empty-btn:hover, .secondary-btn:hover { background-color: #d1d5db; }

        .success-message { background-color: #dcfce7; color: #166534; border: 1px solid #bbf7d0; padding: 0.75rem; border-radius: 6px; margin-top: 1rem; font-size: 0.875rem; }

        .storage-chart { width: 100%; height: 40px; background: linear-gradient(to right, #2563eb 35%, #e5e7eb 35%); border-radius: 8px; margin-bottom: 1rem; }

        .toggle-switch { display:inline-flex; align-items:center; width:48px; height:24px; background:#d1d5db; border-radius:12px; padding:2px; cursor:pointer; transition: background 0.2s; }
        .toggle-switch.active { background: #2563eb; }
        .toggle-switch-circle { width:20px; height:20px; background:white; border-radius:50%; transition: transform 0.2s; }
        .toggle-switch.active .toggle-switch-circle { transform: translateX(24px); }

        .icon-box { display:inline-flex; align-items:center; justify-content:center; width:40px; height:40px; background-color:#e5e7eb; border-radius:6px; margin-right:1rem; }
        .icon-box svg { width:20px; height:20px; }

        .device-item { display:flex; align-items:center; justify-content:space-between; padding:1rem 0; border-bottom:1px solid #e5e7eb; }
        .device-item:last-child { border-bottom: none; }
        .remove-btn { background:none; border:none; color:#dc2626; cursor:pointer; font-size:1.25rem; padding:0; width:24px; height:24px; display:flex; align-items:center; justify-content:center; }

        .modal-overlay { position: fixed; inset:0; background-color: rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100; }
        .modal-content { background:#fff; border-radius:8px; padding:1.5rem; max-width:400px; width:90%; box-shadow:0 10px 40px rgba(0,0,0,0.15); }
        .modal-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; }
        .modal-title { font-size:1.25rem; font-weight:600; color:#0f172a; }
        .modal-close-btn { background:none; border:none; cursor:pointer; display:flex; padding:0; }
        .modal-close-btn svg { color:#dc2626; width:1.5rem; height:1.5rem; }
        .modal-text { font-size:0.875rem; color:#64748b; margin-bottom:1.5rem; line-height:1.6; }
        .warning-text { color:#dc2626; font-weight:600; }
        .modal-buttons { display:flex; gap:0.75rem; justify-content:flex-end; }
        .modal-btn { padding:0.5rem 1rem; border-radius:6px; cursor:pointer; font-weight:500; font-size:0.875rem; border:none; transition: background-color 0.2s; }
        .modal-btn-cancel { background-color:#e5e7eb; color:#0f172a; }
        .modal-btn-cancel:hover { background-color:#d1d5db; }
        .modal-btn-delete { background-color:#dc2626; color:#fff; }
        .modal-btn-delete:hover { background-color:#b91c1c; }

        .recovery-phrase-box { background-color:#f9fafb; border:1px solid #e5e7eb; border-radius:6px; padding:1rem; font-family:monospace; font-size:0.875rem; word-break:break-all; color:#0f172a; }

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
              className={`sidebar-btn ${idx === 4 ? "active" : ""}`}
              onClick={() => routerNavigate(item.to)}
            >
              <img 
                src={item.icon} 
                alt="" 
                style={{ width: "1.1rem", height: "1.1rem", flexShrink: 0 }} 
              />
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
                if (emailError) setEmailError("");
              }}
              className="input-field"
              style={{ marginBottom: "1.5rem" }}
            />

            <label style={{ display: "block", marginBottom: "0.5rem", fontSize: "0.875rem", fontWeight: "500", color: "#374151" }}>
              Email
            </label>
            <input
              type="email"
              value={tempEmail}
              onChange={(e) => {
                setTempEmail(e.target.value);
                if (emailError) setEmailError("");
              }}
              className="input-field"
              style={{ marginBottom: "2rem" }}
            />

            <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
              <button className="update-btn" onClick={handleUpdateProfile} style={{ flexShrink: 0 }}>
                Update Profile
              </button>
              {successMessage.includes("Profile updated") && <div className="success-message" style={{ marginTop: 0 }}>{successMessage}</div>}
            </div>
            {emailError && <div style={{ color: "#dc2626", fontSize: "0.875rem", marginTop: "0.75rem" }}>{emailError}</div>}
          </div>
        </section>

        {/* Storage Section */}
        <section ref={storageRef} style={{ marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>
            Storage
          </h2>

          <div style={{ maxWidth: "500px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "1rem" }}>
              <span style={{ fontSize: "0.875rem", color: "#64748b" }}>Storage Used</span>
              <span style={{ fontSize: "0.875rem", fontWeight: "600", color: "#0f172a" }}>35%</span>
            </div>

            <div className="storage-chart" />

            <p style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: "1.5rem" }}>
              3.5 GB of 10 GB used (Free Plan)
            </p>

            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>
              Manage Storage
            </h3>

            <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem", marginBottom: "1.5rem" }}>
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: "0.875rem", fontWeight: "600", color: "#0f172a", marginBottom: "0.25rem" }}>
                  Empty Trash
                </h4>
                <p style={{ fontSize: "0.75rem", color: "#64748b", marginBottom: "1rem" }}>
                  Files in your trash are automatically deleted after 30 days.
                </p>
                <div style={{ display: "flex", alignItems: "flex-start", gap: "1rem" }}>
                  <button className="empty-btn" onClick={handleEmptyTrash}>
                    Empty
                  </button>
                  {successMessage.includes("Trash emptied") && <div className="success-message" style={{ marginTop: 0 }}>{successMessage}</div>}
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Security Section */}
        <section ref={securityRef} style={{ marginBottom: "4rem" }}>
          <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>
            Security
          </h2>

          <div style={{ maxWidth: "500px" }}>
            {/* Two-Factor Authentication */}
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>
              Two-step Authentication
            </h3>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px" }}>
              <div style={{ display: "flex", alignItems: "center" }}>
                <div className="icon-box">
                  <img src={SecurityIcon} alt="Authenticator" style={{ width: "20px", height: "20px" }} />
                </div>
                <div>
                  <p style={{ fontSize: "0.875rem", fontWeight: "500", color: "#0f172a", marginBottom: "0.25rem" }}>
                    Use an authenticator app
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "#64748b" }}>
                    Get a verification code when you sign in
                  </p>
                </div>
              </div>
              <div
                className={`toggle-switch ${enable2FA ? "active" : ""}`}
                onClick={() => setEnable2FA(!enable2FA)}
              >
                <div className="toggle-switch-circle"></div>
              </div>
            </div>

            {/* Recovery Phrase */}
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>
              Recovery Phrase
            </h3>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "2rem", padding: "1rem", backgroundColor: "#f9fafb", borderRadius: "6px" }}>
              <div style={{ display: "flex", alignItems: "center" }}>
                <div className="icon-box">
                  <img src={KeyIcon} alt="Key" style={{ width: "20px", height: "20px" }} />
                </div>
                <div>
                  <p style={{ fontSize: "0.875rem", fontWeight: "500", color: "#0f172a", marginBottom: "0.25rem" }}>
                    Recovery Phrase
                  </p>
                  <p style={{ fontSize: "0.75rem", color: "#64748b" }}>
                    If you lose access to your account, you can use your recovery phrase to get back in.
                  </p>
                </div>
              </div>
              <button className="secondary-btn" onClick={handleRegenerateRecovery} style={{ flexShrink: 0 }}>
                Regenerate
              </button>
            </div>

            {/* Trusted Devices */}
            <h3 style={{ fontSize: "1rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>
              Trusted Devices
            </h3>
            <div style={{ marginBottom: "1.5rem" }}>
              {devices.map((device, idx) => (
                <div key={device.id} className="device-item" style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "1rem 0", borderBottom: idx === devices.length - 1 ? "none" : "1px solid #e5e7eb" }}>
                  <div>
                    <p style={{ fontSize: "0.875rem", fontWeight: "500", color: "#0f172a", marginBottom: "0.25rem" }}>
                      {device.name}
                    </p>
                    <p style={{ fontSize: "0.75rem", color: "#64748b" }}>
                      {device.date}
                    </p>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    {idx === 0 && (
                      <p style={{ fontSize: "0.65rem", color: "#64748b", textAlign: "right", margin: 0, lineHeight: "1.2", marginRight: "0.5rem" }}>
                        If it is not you,<br />logout by clicking
                      </p>
                    )}
                    <button 
                      onClick={() => handleRemoveDevice(device.id)}
                      title="Remove device"
                      style={{
                        background: "none",
                        border: "none",
                        color: "#dc2626",
                        cursor: "pointer",
                        fontSize: "1.25rem",
                        padding: "0",
                        width: "24px",
                        height: "24px",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        flexShrink: 0
                      }}
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <button className="secondary-btn" onClick={handleLogoutAllDevices}>
              Log out from all devices
            </button>

            {successMessage && !successMessage.includes("Profile updated") && !successMessage.includes("Trash emptied") && <div className="success-message" style={{ marginTop: "1rem" }}>{successMessage}</div>}
          </div>
        </section>
      </main>

      {/* Empty Trash Confirmation Modal */}
      {emptyTrashWarning && (
        <div className="modal-overlay" onClick={() => setEmptyTrashWarning(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Empty Trash?</h2>
              <button className="modal-close-btn" onClick={() => setEmptyTrashWarning(false)}>
                <X />
              </button>
            </div>

            <div className="modal-text">
              Are you sure you want to <span className="warning-text">permanently delete</span> all files in your trash? This action cannot be undone.
            </div>

            <div className="modal-buttons">
              <button className="modal-btn modal-btn-cancel" onClick={() => setEmptyTrashWarning(false)}>
                No, Cancel
              </button>
              <button className="modal-btn modal-btn-delete" onClick={confirmEmptyTrash}>
                Yes, Empty Trash
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Remove Device Confirmation Modal */}
      {removeDeviceWarning && (
        <div className="modal-overlay" onClick={() => setRemoveDeviceWarning(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Remove Device?</h2>
              <button className="modal-close-btn" onClick={() => setRemoveDeviceWarning(false)}>
                <X />
              </button>
            </div>

            <div className="modal-text">
              Are you sure you want to <span className="warning-text">log out</span> from this device? You will need to sign in again.
            </div>

            <div className="modal-buttons">
              <button className="modal-btn modal-btn-cancel" onClick={() => setRemoveDeviceWarning(false)}>
                No, Cancel
              </button>
              <button className="modal-btn modal-btn-delete" onClick={confirmRemoveDevice}>
                Yes, Remove Device
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Recovery Phrase Modal */}
      {recoveryPhraseModal && (
        <div className="modal-overlay" onClick={() => setRecoveryPhraseModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Recovery Phrase</h2>
              <button className="modal-close-btn" onClick={() => setRecoveryPhraseModal(false)}>
                <X />
              </button>
            </div>

            <div className="recovery-phrase-box">
              {RECOVERY_PHRASE}
            </div>

            <p style={{ fontSize: "0.75rem", color: "#64748b", marginTop: "1rem", textAlign: "center" }}>
              Save this phrase in a safe place. You'll need it to recover your account.
            </p>
          </div>
        </div>
      )}

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
                  <img src={item.icon} alt="" style={{ width: "1rem", height: "1rem" }} />
                  <span>{item.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>
      )}
    </TopNavBar>
  );
}
