import React, { useState, useEffect } from "react";
import { X, Calendar } from "lucide-react";
import api from "../services/api";

const CalendarPicker = ({ onDateSelect, currentDate }) => {
  const [pickerMonth, setPickerMonth] = useState(currentDate.getMonth());
  const [pickerYear, setPickerYear] = useState(currentDate.getFullYear());

  const daysInMonth = (month, year) => new Date(year, month + 1, 0).getDate();
  const firstDay = new Date(pickerYear, pickerMonth, 1).getDay();
  const days = Array.from({ length: daysInMonth(pickerMonth, pickerYear) }, (_, i) => i + 1);
  const weeks = [];
  let currentWeek = Array(firstDay).fill(null);

  days.forEach(day => {
    currentWeek.push(day);
    if (currentWeek.length === 7) {
      weeks.push(currentWeek);
      currentWeek = [];
    }
  });
  if (currentWeek.length > 0) weeks.push(currentWeek);

  return (
    <div style={{
      display: "flex",
      flexDirection: "column",
      width: "100%"
    }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
        <button onClick={() => setPickerMonth(m => m === 0 ? 11 : m - 1)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "14px" }}>←</button>
        <span style={{ fontSize: "14px", fontWeight: 600 }}>
          {new Date(pickerYear, pickerMonth).toLocaleString('default', { month: 'long', year: 'numeric' })}
        </span>
        <button onClick={() => setPickerMonth(m => m === 11 ? 0 : m + 1)} style={{ background: "none", border: "none", cursor: "pointer", fontSize: "14px" }}>→</button>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(7, 1fr)", gap: "4px" }}>
        {["S", "M", "T", "W", "T", "F", "S"].map(day => (
          <div key={day} style={{ textAlign: "center", fontSize: "12px", fontWeight: 600, color: "#64748b" }}>{day}</div>
        ))}
        {weeks.map((week, idx) => week.map((day, dayIdx) => (
          <button
            key={`${idx}-${dayIdx}`}
            onClick={() => day && onDateSelect(day, pickerMonth, pickerYear)}
            style={{
              padding: "6px",
              border: day ? "1px solid #e5e7eb" : "none",
              borderRadius: "4px",
              background: day ? "#fff" : "transparent",
              cursor: day ? "pointer" : "default",
              fontSize: "12px",
              color: day ? "#0f172a" : "transparent"
            }}
          >
            {day}
          </button>
        )))}
      </div>
    </div>
  );
};

export default function FolderShareModal({ folder, onClose }) {
  const [shareEmail, setShareEmail] = useState("");
  const [shareExpiryDate, setShareExpiryDate] = useState("");
  const [permission, setPermission] = useState("view");
  const [generatePublicLink, setGeneratePublicLink] = useState(false);
  const [maxDownloads, setMaxDownloads] = useState("");
  const [publicLinkPassword, setPublicLinkPassword] = useState("");
  const [shareLoading, setShareLoading] = useState(false);
  const [emailError, setEmailError] = useState("");
  const [dateError, setDateError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [shareError, setShareError] = useState("");
  const [publicLinks, setPublicLinks] = useState([]);
  const [linksLoading, setLinksLoading] = useState(false);
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(new Date());

  useEffect(() => {
    if (folder?.id) {
      loadLinks();
    }
  }, [folder]);

  const loadLinks = async () => {
    try {
      setLinksLoading(true);
      const data = await api.getPublicFolderLinks(folder.id);
      const activeLinks = (data.links || []).filter(link => link.active !== false);
      setPublicLinks(activeLinks);
    } catch (err) {
      console.error("Failed to load links", err);
      setPublicLinks([]);
    } finally {
      setLinksLoading(false);
    }
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateDate = (dateStr) => {
    if (!dateStr) return false;
    const dateRegex = /^(\d{2}|\d{4})\/\d{2}\/\d{2}$/;
    if (!dateRegex.test(dateStr)) return false;
    
    const parts = dateStr.split('/');
    let year = parseInt(parts[0]);
    const month = parseInt(parts[1]);
    const day = parseInt(parts[2]);
    
    if (parts[0].length === 2) {
      year += year < 50 ? 2000 : 1900;
    }
    
    const date = new Date(year, month - 1, day);
    return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
  };

  const handleCreateShareLink = async () => {
    let hasError = false;

    if (!generatePublicLink && !shareEmail) {
      setEmailError("Email is required");
      hasError = true;
    } else if (!generatePublicLink && !validateEmail(shareEmail)) {
      setEmailError("Invalid email format");
      hasError = true;
    } else {
      setEmailError("");
    }

    if (shareExpiryDate && !validateDate(shareExpiryDate)) {
      setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
      hasError = true;
    } else {
      setDateError("");
    }

    if (hasError) return;

    setShareLoading(true);
    setShareError("");

    try {
      if (generatePublicLink) {
        let expirationDate = null;
        if (shareExpiryDate) {
          const parts = shareExpiryDate.split('/');
          let year = parseInt(parts[0]);
          const month = parseInt(parts[1]);
          const day = parseInt(parts[2]);
          
          if (parts[0].length === 2) {
            year += year < 50 ? 2000 : 1900;
          }
          
          expirationDate = new Date(year, month - 1, day).toISOString();
        }

        const result = await api.createPublicFolderLink(folder.id, {
          password: publicLinkPassword || null,
          expiresAt: expirationDate,
          maxDownloads: maxDownloads ? parseInt(maxDownloads) : null
        });

        const link = `${window.location.origin}/public/folders/${result.token}`;
        setSuccessMessage(`✓ Public link created!\n${link}`);
        setPublicLinkPassword("");
        setMaxDownloads("");
        setShareExpiryDate("");
        setGeneratePublicLink(false);
        
        await loadLinks();
        setTimeout(() => setSuccessMessage(""), 5000);
      } else {
        await api.shareFolder(folder.id, [shareEmail], permission);
        setSuccessMessage(`✓ Invitation sent to ${shareEmail}`);
        setShareEmail("");
        setTimeout(() => setSuccessMessage(""), 3000);
      }
    } catch (err) {
      setShareError(err.message || "Failed to create share");
    } finally {
      setShareLoading(false);
    }
  };

  const handleCalendarDateSelect = (day, month, year) => {
    const dateStr = `${String(year).slice(-2)}/${String(month + 1).padStart(2, '0')}/${String(day).padStart(2, '0')}`;
    setShareExpiryDate(dateStr);
    setShowCalendar(false);
  };

  const handleDeletePublicLink = async (linkId) => {
    try {
      await api.deletePublicFolderLink(folder.id, linkId);
      setPublicLinks(publicLinks.filter(link => link.link_id !== linkId));
      setSuccessMessage("✓ Public link deleted");
      setTimeout(() => setSuccessMessage(""), 2000);
    } catch (err) {
      setShareError("Failed to delete link: " + (err.message || "Unknown error"));
    }
  };

  if (!folder) return null;

  return (
    <div
      style={{
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
        overflow: "auto"
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: "white",
          padding: "1.5rem",
          borderRadius: "8px",
          maxWidth: "500px",
          width: "90%",
          maxHeight: "90vh",
          overflow: "auto",
          margin: "auto",
          boxShadow: "0 10px 40px rgba(0, 0, 0, 0.15)"
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "1rem" }}>
          <h2 style={{ fontSize: "1.25rem", fontWeight: 600, color: "#0f172a", margin: 0 }}>
            Share "{folder.name}"
          </h2>
          <button
            onClick={onClose}
            style={{
              background: "none",
              border: "none",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              padding: 0
            }}
          >
            <X style={{ color: "#dc2626", width: "1.5rem", height: "1.5rem" }} />
          </button>
        </div>

        <div style={{ marginBottom: "1.5rem" }}>
          {/* Email Input - Hidden when generating public link */}
          {!generatePublicLink && (
            <div style={{ marginBottom: "1rem", position: "relative" }}>
              <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Email</label>
              <input
                type="email"
                placeholder="Enter email"
                value={shareEmail}
                onChange={(e) => {
                  setShareEmail(e.target.value);
                  if (emailError) setEmailError("");
                }}
                style={{
                  width: "100%",
                  border: emailError ? "1px solid #dc2626" : "1px solid #d1d5db",
                  borderRadius: "6px",
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.875rem",
                  background: "transparent",
                  outline: "none",
                  transition: "border-color 0.2s",
                  height: "2.5rem",
                  boxSizing: "border-box"
                }}
                disabled={shareLoading}
              />
              {emailError && <span style={{ color: "#dc2626", fontSize: "0.75rem", marginTop: "0.25rem", display: "block" }}>{emailError}</span>}
            </div>
          )}

          {/* Expiry Date Input */}
          <div style={{ marginBottom: "1rem", position: "relative" }}>
            <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Expiry Date</label>
            <div style={{ position: "relative" }}>
              <input
                type="text"
                placeholder="YY/MM/DD"
                value={shareExpiryDate}
                onChange={(e) => {
                  setShareExpiryDate(e.target.value);
                  if (dateError) setDateError("");
                }}
                style={{
                  width: "100%",
                  border: dateError ? "1px solid #dc2626" : "1px solid #d1d5db",
                  borderRadius: "6px",
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.875rem",
                  background: "transparent",
                  outline: "none",
                  transition: "border-color 0.2s",
                  height: "2.5rem",
                  boxSizing: "border-box",
                  paddingRight: "2.5rem"
                }}
                disabled={shareLoading}
              />
              <button
                onClick={() => setShowCalendar(!showCalendar)}
                style={{
                  position: "absolute",
                  right: "0.75rem",
                  top: "50%",
                  transform: "translateY(-50%)",
                  background: "none",
                  border: "none",
                  cursor: "pointer",
                  padding: 0,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center"
                }}
              >
                <Calendar style={{ width: "18px", height: "18px", color: "#64748b" }} />
              </button>
              {showCalendar && (
                <div style={{
                  position: "absolute",
                  top: "100%",
                  right: 0,
                  marginTop: "8px",
                  background: "#fff",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  padding: "12px",
                  boxShadow: "0 4px 12px rgba(0,0,0,0.1)",
                  zIndex: 200,
                  minWidth: "280px"
                }}>
                  <CalendarPicker onDateSelect={handleCalendarDateSelect} currentDate={calendarDate} />
                </div>
              )}
            </div>
            {dateError && <span style={{ color: "#dc2626", fontSize: "0.75rem", marginTop: "0.25rem", display: "block" }}>{dateError}</span>}
          </div>

          {/* Generate Public Link Toggle */}
          <div style={{ marginBottom: "1rem", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <label style={{ color: "#374151", fontSize: "0.875rem", fontWeight: 500, marginBottom: 0 }}>Generate public link</label>
            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                width: "48px",
                height: "24px",
                background: generatePublicLink ? "#2563eb" : "#d1d5db",
                borderRadius: "12px",
                padding: "2px",
                cursor: "pointer",
                transition: "background 0.2s"
              }}
              onClick={() => setGeneratePublicLink(!generatePublicLink)}
            >
              <div
                style={{
                  width: "20px",
                  height: "20px",
                  background: "white",
                  borderRadius: "50%",
                  transition: "transform 0.2s",
                  transform: generatePublicLink ? "translateX(24px)" : "translateX(0)"
                }}
              ></div>
            </div>
          </div>

          {/* Max Downloads Input */}
          <div style={{ marginBottom: "1rem", position: "relative" }}>
            <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Max downloads</label>
            <input
              type="number"
              placeholder="Unlimited"
              value={maxDownloads}
              onChange={(e) => setMaxDownloads(e.target.value.replace(/[^0-9]/g, ""))}
              min="1"
              style={{
                width: "100%",
                border: "1px solid #d1d5db",
                borderRadius: "6px",
                padding: "0.5rem 0.75rem",
                fontSize: "0.875rem",
                background: "transparent",
                outline: "none",
                transition: "border-color 0.2s",
                height: "2.5rem",
                boxSizing: "border-box"
              }}
              disabled={shareLoading}
            />
          </div>

          {/* Password Input (only for public links) */}
          {generatePublicLink && (
            <div style={{ marginBottom: "1.5rem" }}>
              <label style={{ display: "block", marginBottom: "0.25rem", color: "#374151", fontSize: "0.875rem", fontWeight: 500 }}>Password (optional)</label>
              <input
                type="password"
                placeholder="Leave empty for no password"
                value={publicLinkPassword}
                onChange={(e) => setPublicLinkPassword(e.target.value)}
                style={{
                  width: "100%",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  padding: "0.5rem 0.75rem",
                  fontSize: "0.875rem",
                  background: "transparent",
                  outline: "none",
                  transition: "border-color 0.2s",
                  height: "2.5rem",
                  boxSizing: "border-box"
                }}
                disabled={shareLoading}
              />
            </div>
          )}

          {/* Create Share Link Button */}
          <button
            onClick={handleCreateShareLink}
            style={{
              width: "100%",
              padding: "0.5rem 1rem",
              backgroundColor: "#2563eb",
              color: "white",
              border: "none",
              borderRadius: "6px",
              fontSize: "0.875rem",
              fontWeight: 500,
              cursor: "pointer",
              height: "2.5rem",
              opacity: shareLoading ? 0.6 : 1,
              pointerEvents: shareLoading ? "none" : "auto",
              transition: "background-color 0.2s"
            }}
            disabled={shareLoading}
            onMouseEnter={(e) => !shareLoading && (e.target.style.backgroundColor = "#1d4ed8")}
            onMouseLeave={(e) => !shareLoading && (e.target.style.backgroundColor = "#2563eb")}
          >
            {shareLoading ? "Creating..." : generatePublicLink ? "Create public link" : "Create share link"}
          </button>

          {successMessage && (
            <div style={{
              marginTop: "1rem",
              padding: "0.75rem",
              backgroundColor: "#dcfce7",
              color: "#166534",
              borderRadius: "6px",
              fontSize: "0.875rem",
              border: "1px solid #bbf7d0",
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.75rem"
            }}>
              <span style={{ flex: 1, whiteSpace: "pre-wrap", wordBreak: "break-all" }}>{successMessage}</span>
              <button
                onClick={() => {
                  const linkText = successMessage.split('\n')[1];
                  navigator.clipboard.writeText(linkText);
                  setSuccessMessage("✓ Link copied to clipboard!");
                  setTimeout(() => setSuccessMessage(""), 2000);
                }}
                style={{
                  padding: "0.4rem 0.8rem",
                  backgroundColor: "#bbf7d0",
                  color: "#166534",
                  border: "none",
                  borderRadius: "4px",
                  cursor: "pointer",
                  fontSize: "0.75rem",
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                  flexShrink: 0,
                  transition: "background-color 0.2s"
                }}
                onMouseEnter={(e) => e.target.style.backgroundColor = "#86efac"}
                onMouseLeave={(e) => e.target.style.backgroundColor = "#bbf7d0"}
              >
                Copy
              </button>
            </div>
          )}

          {shareError && (
            <div style={{
              marginTop: "1rem",
              padding: "0.75rem",
              backgroundColor: "#fee2e2",
              color: "#7f1d1d",
              borderRadius: "6px",
              fontSize: "0.875rem",
              border: "1px solid #fecaca"
            }}>
              {shareError}
            </div>
          )}

          {/* Existing Public Links Section */}
          {linksLoading && (
            <div style={{
              marginTop: "1.5rem",
              padding: "1rem",
              backgroundColor: "#f3f4f6",
              borderRadius: "6px",
              textAlign: "center",
              color: "#64748b",
              fontSize: "0.875rem"
            }}>
              Loading links...
            </div>
          )}

          {!linksLoading && publicLinks.length > 0 && (
            <div style={{ marginTop: "1.5rem" }}>
              <h3 style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151", marginBottom: "0.75rem", marginTop: 0 }}>Existing public links</h3>
              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                {publicLinks.map((link) => (
                  <div key={link.link_id} style={{
                    padding: "0.75rem",
                    backgroundColor: "#f9fafb",
                    border: "1px solid #e5e7eb",
                    borderRadius: "6px"
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "0.75rem" }}>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <input
                          readOnly
                          value={`${window.location.origin}/public/folders/${link.token}`}
                          style={{
                            width: "100%",
                            border: "1px solid #d1d5db",
                            borderRadius: "4px",
                            padding: "0.5rem",
                            fontSize: "0.75rem",
                            backgroundColor: "white",
                            color: "#374151",
                            fontFamily: "monospace"
                          }}
                        />
                      </div>
                      <button
                        onClick={() => {
                          navigator.clipboard.writeText(`${window.location.origin}/public/folders/${link.token}`);
                          setSuccessMessage("✓ Link copied!");
                          setTimeout(() => setSuccessMessage(""), 2000);
                        }}
                        style={{
                          padding: "0.4rem 0.8rem",
                          backgroundColor: "#f3f4f6",
                          color: "#374151",
                          border: "1px solid #d1d5db",
                          borderRadius: "4px",
                          cursor: "pointer",
                          fontSize: "0.75rem",
                          fontWeight: 500,
                          whiteSpace: "nowrap",
                          flexShrink: 0
                        }}
                      >
                        Copy
                      </button>
                      <button
                        onClick={() => handleDeletePublicLink(link.link_id)}
                        style={{
                          padding: "0.4rem 0.8rem",
                          backgroundColor: "#fee2e2",
                          color: "#dc2626",
                          border: "none",
                          borderRadius: "4px",
                          cursor: "pointer",
                          fontSize: "0.75rem",
                          fontWeight: 500,
                          whiteSpace: "nowrap",
                          flexShrink: 0
                        }}
                      >
                        Delete
                      </button>
                    </div>
                    {link.password_protected && (
                      <div style={{ marginTop: "0.5rem", fontSize: "0.75rem", color: "#b45309" }}>
                        🔒 Password protected
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
