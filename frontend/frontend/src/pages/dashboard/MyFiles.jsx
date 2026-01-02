import React, { useState } from "react";
import { Search, X, Calendar } from "lucide-react";
import TopNavBar from "../../layout/TopNavBar";
import DashboardIcon from "../../resources/icons/dashboard.svg";
import MyFilesIcon from "../../resources/icons/my_files.svg";
import SharedIcon from "../../resources/icons/shared.svg";
import TrashIcon from "../../resources/icons/trash.svg";
import SettingsIcon from "../../resources/icons/settings.svg";

const navItems = [
  { icon: DashboardIcon, label: "Dashboard", to: "/dashboard" },
  { icon: MyFilesIcon, label: "My Files", to: "/my-files" },
  { icon: SharedIcon, label: "Shared", to: "/shared" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

// Sample files sorted by last accessed (newest first)
const SAMPLE_MY_FILES = [
  { id: 1, name: "Document 1", owner: "You", lastAccessed: "2025-08-20 14:30", size: "2.5 MB", uploadDate: "2025-08-15", hash: "a1b2c3d4e5f6", encryption: "AES-256", downloads: 5 },
  { id: 2, name: "Presentation 1", owner: "You", lastAccessed: "2025-08-19 10:15", size: "5.8 MB", uploadDate: "2025-07-20", hash: "f6e5d4c3b2a1", encryption: "AES-256", downloads: 12 },
  { id: 3, name: "Spreadsheet 1", owner: "You", lastAccessed: "2025-08-18 09:45", size: "3.1 MB", uploadDate: "2025-08-05", hash: "c3b2a1f6e5d4", encryption: "AES-256", downloads: 3 },
  { id: 4, name: "Image 1", owner: "You", lastAccessed: "2025-08-17 16:20", size: "1.2 MB", uploadDate: "2025-08-10", hash: "e5d4c3b2a1f6", encryption: "AES-256", downloads: 8 },
  { id: 5, name: "Video 1", owner: "You", lastAccessed: "2025-08-16 11:00", size: "15.9 MB", uploadDate: "2025-07-10", hash: "b2a1f6e5d4c3", encryption: "AES-256", downloads: 2 },
];

export default function MyFiles() {
  const [searchQuery, setSearchQuery] = useState("");
  const [appliedSearch, setAppliedSearch] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [shareFile, setShareFile] = useState(null);
  const [shareEmail, setShareEmail] = useState("");
  const [shareExpiryDate, setShareExpiryDate] = useState("");
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [generatePublicLink, setGeneratePublicLink] = useState(false);
  const [maxDownloads, setMaxDownloads] = useState("");
  const [emailError, setEmailError] = useState("");
  const [dateError, setDateError] = useState("");

  let displayFiles = SAMPLE_MY_FILES;

  // Apply search
  if (appliedSearch && appliedSearch.length > 0) {
    const q = appliedSearch.toLowerCase();
    displayFiles = displayFiles.filter((f) => f.name.toLowerCase().includes(q));
  }

  const handleDownload = (file) => {
    alert(`Downloading: ${file.name}`);
  };

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateDate = (dateStr) => {
    if (!dateStr) return false;
    // Accept YY/MM/DD or YYYY/MM/DD format
    const dateRegex = /^(\d{2}|\d{4})\/\d{2}\/\d{2}$/;
    if (!dateRegex.test(dateStr)) return false;
    
    const parts = dateStr.split('/');
    let year = parseInt(parts[0]);
    const month = parseInt(parts[1]);
    const day = parseInt(parts[2]);
    
    // Convert 2-digit year to 4-digit
    if (parts[0].length === 2) {
      year += year < 50 ? 2000 : 1900;
    }
    
    // Basic date validity check
    const date = new Date(year, month - 1, day);
    return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
  };

  const handleCreateShareLink = () => {
    let hasError = false;
    
    // Validate email
    if (!shareEmail) {
      setEmailError("Email is required");
      hasError = true;
    } else if (!validateEmail(shareEmail)) {
      setEmailError("Please enter a valid email address");
      hasError = true;
    } else {
      setEmailError("");
    }
    
    // Validate date
    if (!shareExpiryDate) {
      setDateError("Expiry date is required");
      hasError = true;
    } else if (!validateDate(shareExpiryDate)) {
      setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
      hasError = true;
    } else {
      setDateError("");
    }
    
    if (hasError) return;

    alert(`Share link created for ${shareFile.name}\nEmail: ${shareEmail}\nExpiry: ${shareExpiryDate}\nPublic Link: ${generatePublicLink}\nMax Downloads: ${maxDownloads}`);
    setShareFile(null);
  };

  const handleShare = (file) => {
    setShareFile(file);
    setShareEmail("");
    setShareExpiryDate("");
    setGeneratePublicLink(false);
    setMaxDownloads("");
    setEmailError("");
    setDateError("");
  };

  const handleCalendarDateSelect = (day, month, year) => {
    const dateStr = `${String(year).slice(-2)}/${String(month + 1).padStart(2, '0')}/${String(day).padStart(2, '0')}`;
    setShareExpiryDate(dateStr);
    setShowCalendar(false);
  };

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
        .sidebar-btn:hover {
          background-color: #f1f5f9;
        }
        .sidebar-btn.active {
          background-color: #e2e8f0;
          color: #0f172a;
          font-weight: 500;
        }
        .file-link {
          color: #2563eb;
          text-decoration: underline;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        .file-link:hover {
          opacity: 0.7;
        }
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background-color: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 100;
        }
        .modal-content {
          background: #ffffff;
          border-radius: 8px;
          padding: 1.5rem;
          max-width: 500px;
          width: 90%;
          box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
        }
        .modal-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 1rem;
        }
        .modal-title {
          font-size: 1.25rem;
          font-weight: 600;
          color: #0f172a;
        }
        .modal-close-btn {
          background: none;
          border: none;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 0;
        }
        .modal-close-btn svg {
          color: #dc2626;
          width: 1.5rem;
          height: 1.5rem;
        }
        .modal-info {
          margin-bottom: 1.5rem;
        }
        .modal-info-row {
          display: flex;
          justify-content: space-between;
          padding: 0.5rem 0;
          border-bottom: 1px solid #e5e7eb;
          font-size: 0.875rem;
        }
        .modal-info-label {
          font-weight: 500;
          color: #64748b;
        }
        .modal-info-value {
          color: #0f172a;
        }
        .modal-buttons {
          display: flex;
          gap: 0.5rem;
          justify-content: flex-end;
        }
        .modal-btn {
          background-color: #2563eb;
          color: #ffffff;
          border: none;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 500;
          font-size: 0.875rem;
          transition: background-color 0.2s;
        }
        .modal-btn:hover {
          background-color: #1d4ed8;
        }
        .search-wrapper {
          width: 90%;
          max-width: 90%;
          margin-left: 0;
        }
        .content-width { 
          width: 90%; 
          max-width: 90%; 
          margin-left: 0; 
        }
        .files-table { 
          border: 1px solid #e5e7eb; 
          border-radius: 8px; 
          overflow: hidden; 
        }
        .files-table > .table-inner { 
          padding: 0 0.5rem 0.5rem 0.5rem; 
        }
        .files-table thead tr { 
          border-bottom: 1px solid #e5e7eb; 
        }
        .files-table tbody tr { 
          border-bottom: 1px solid #e5e7eb; 
        }
        .files-table th, .files-table td { 
          padding-left: 1rem; 
          padding-right: 1rem; 
        }
        .files-table thead th { 
          padding-top: 0.45rem; 
          padding-bottom: 0.6rem; 
          text-align: left; 
          vertical-align: middle; 
        }
        .files-table th:last-child, .files-table td:last-child { 
          border-right: none; 
        }
        .col-muted { 
          color: #64748b; 
        }
        .files-table .table-inner table { 
          width: 100%; 
        }
        .share-input {
          width: 100%;
          border: 1px solid #d1d5db;
          border-radius: 6px;
          padding: 0.5rem 0.75rem;
          font-size: 0.875rem;
          background: transparent;
          outline: none;
          transition: border-color 0.2s;
          height: 2.5rem;
        }
        .share-input:focus {
          border-color: #2563eb;
        }
        .share-input-group {
          margin-bottom: 1rem;
          position: relative;
        }
        .share-input-label {
          font-size: 0.875rem;
          font-weight: 500;
          color: #374151;
          margin-bottom: 0.25rem;
          display: block;
        }
        .toggle-switch {
          display: inline-flex;
          align-items: center;
          width: 48px;
          height: 24px;
          background: #d1d5db;
          border-radius: 12px;
          padding: 2px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .toggle-switch.active {
          background: #2563eb;
        }
        .toggle-switch-circle {
          width: 20px;
          height: 20px;
          background: white;
          border-radius: 50%;
          transition: transform 0.2s;
        }
        .toggle-switch.active .toggle-switch-circle {
          transform: translateX(24px);
        }
        .share-modal-btn {
          width: 100%;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          border: 1px solid #d1d5db;
          background: transparent;
          color: #0f172a;
          transition: all 0.2s;
          height: 2.5rem;
        }
        .share-modal-btn:hover {
          border-color: #9ca3af;
        }
        .share-modal-btn.primary {
          background: #2563eb;
          color: white;
          border: none;
          width: 100%;
        }
        .share-modal-btn.primary:hover {
          background: #1d4ed8;
        }
        .calendar-icon-btn {
          position: absolute;
          right: 0.75rem;
          top: 50%;
          transform: translateY(-50%);
          background: none;
          border: none;
          cursor: pointer;
          padding: 0;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .error-text {
          color: #dc2626;
          font-size: 0.75rem;
          margin-top: 0.25rem;
          display: block;
        }
      `}</style>

      {/* Sidebar */}
      <aside 
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
              className={`sidebar-btn ${idx === 1 ? "active" : ""}`}
              onClick={() => window.location.href = item.to}
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
        <header style={{ marginBottom: "3rem" }}>
          <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "#0f172a" }}>My Files</h1>
        </header>

        {/* Search Bar */}
        <div className="search-wrapper" style={{ marginBottom: "0.3cm", display: "flex", alignItems: "center", gap: "0.25cm" }}>
          <Search style={{ width: "1.25rem", height: "1.25rem", color: "#9ca3af", flexShrink: 0 }} />
          <input
            type="text"
            placeholder="Search files"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                setAppliedSearch(searchQuery.trim());
              }
            }}
            style={{
              flex: 1,
              backgroundColor: searchQuery ? "#f3f4f6" : "transparent",
              borderRadius: "0.5rem",
              border: "1px solid #e5e7eb",
              padding: "0.35rem 0.75rem",
              height: "1.4rem",
              fontSize: "1rem",
              outline: "none",
              transition: "background-color 0.2s ease",
            }}
            onFocus={(e) => {
              e.target.style.backgroundColor = "#f3f4f6";
            }}
            onBlur={(e) => {
              e.target.style.backgroundColor = searchQuery ? "#f3f4f6" : "transparent";
            }}
          />
        </div>

        {/* Files Table */}
        <div className="files-table content-width" style={{ backgroundColor: "#ffffff", marginTop: "1.5rem" }}>
          <div className="table-inner overflow-x-auto">
            <table style={{ width: "100%", textAlign: "left", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ backgroundColor: "transparent" }}>
                  <th style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Name</th>
                  <th style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Owner</th>
                  <th style={{ fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Last Accessed</th>
                </tr>
              </thead>
              <tbody>
                {displayFiles.map((file) => (
                  <tr key={file.id} style={{ backgroundColor: "#ffffff", height: "2.75rem" }}>
                    <td style={{ fontSize: "0.875rem", fontWeight: 500, color: "#0f172a" }}>
                      <span className="file-link" onClick={() => setSelectedFile(file)}>
                        {file.name}
                      </span>
                    </td>
                    <td style={{ fontSize: "0.875rem", color: "#64748b" }}>{file.owner}</td>
                    <td style={{ fontSize: "0.875rem", color: "#64748b" }}>{file.lastAccessed}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>

      {/* File Details Modal */}
      {selectedFile && !shareFile && (
        <div className="modal-overlay" onClick={() => setSelectedFile(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">File Details</h2>
              <button className="modal-close-btn" onClick={() => setSelectedFile(null)}>
                <X />
              </button>
            </div>

            <div className="modal-info">
              <div className="modal-info-row">
                <span className="modal-info-label">Name:</span>
                <span className="modal-info-value">{selectedFile.name}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">Size:</span>
                <span className="modal-info-value">{selectedFile.size}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">Upload Date:</span>
                <span className="modal-info-value">{selectedFile.uploadDate}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">Owner:</span>
                <span className="modal-info-value">{selectedFile.owner}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">File Hash:</span>
                <span className="modal-info-value" style={{ fontSize: "0.75rem", fontFamily: "monospace" }}>{selectedFile.hash}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">Encryption Status:</span>
                <span className="modal-info-value">{selectedFile.encryption}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">Download Count:</span>
                <span className="modal-info-value">{selectedFile.downloads}</span>
              </div>
              <div className="modal-info-row">
                <span className="modal-info-label">Last Accessed:</span>
                <span className="modal-info-value">{selectedFile.lastAccessed}</span>
              </div>
            </div>

            <div className="modal-buttons">
              <button className="modal-btn" onClick={() => handleDownload(selectedFile)}>
                Download
              </button>
              <button className="modal-btn" onClick={() => handleShare(selectedFile)}>
                Share
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {shareFile && (
        <div className="modal-overlay" onClick={() => setShareFile(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Share "{shareFile.name}"</h2>
              <button className="modal-close-btn" onClick={() => setShareFile(null)}>
                <X />
              </button>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              {/* Email Input */}
              <div className="share-input-group">
                <label className="share-input-label">Email</label>
                <input
                  type="email"
                  placeholder="Enter email"
                  value={shareEmail}
                  onChange={(e) => {
                    setShareEmail(e.target.value);
                    if (emailError) setEmailError("");
                  }}
                  className="share-input"
                />
                {emailError && <span className="error-text">{emailError}</span>}
              </div>

              {/* Expiry Date Input */}
              <div className="share-input-group">
                <label className="share-input-label">Expiry Date</label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    placeholder="YY/MM/DD"
                    value={shareExpiryDate}
                    onChange={(e) => {
                      setShareExpiryDate(e.target.value);
                      if (dateError) setDateError("");
                    }}
                    className="share-input"
                  />
                  <button
                    className="calendar-icon-btn"
                    onClick={() => setShowCalendar(!showCalendar)}
                  >
                    <Calendar style={{ width: "18px", height: "18px", color: "#64748b" }} />
                  </button>
                  {showCalendar && <CalendarPicker onDateSelect={handleCalendarDateSelect} currentDate={calendarDate} />}
                </div>
                {dateError && <span className="error-text">{dateError}</span>}
              </div>

              {/* Generate Public Link Toggle */}
              <div className="share-input-group" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <label className="share-input-label" style={{ marginBottom: 0 }}>Generate public link</label>
                <div
                  className={`toggle-switch ${generatePublicLink ? "active" : ""}`}
                  onClick={() => setGeneratePublicLink(!generatePublicLink)}
                >
                  <div className="toggle-switch-circle"></div>
                </div>
              </div>

              {/* Max Downloads Input */}
              <div className="share-input-group">
                <label className="share-input-label">Max downloads</label>
                <input
                  type="number"
                  placeholder="Unlimited"
                  value={maxDownloads}
                  onChange={(e) => setMaxDownloads(e.target.value.replace(/[^0-9]/g, ""))}
                  min="1"
                  className="share-input"
                />
              </div>

              {/* Create Share Link Button */}
              <button className="share-modal-btn primary" onClick={handleCreateShareLink}>
                Create share link
              </button>
            </div>
          </div>
        </div>
      )}
    </TopNavBar>
  );
}
