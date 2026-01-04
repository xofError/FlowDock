import React, { useState, useEffect } from "react";
import { Search, X, Calendar, Link } from "lucide-react";
import { useNavigate as useRouterNavigate } from "react-router-dom";
import TopNavBar from "../../layout/TopNavBar";
import FileDetailsModal from "../../components/FileDetailsModal";
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

export default function MyFiles() {
  const routerNavigate = useRouterNavigate();
  const { user } = useAuth();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [shareFile, setShareFile] = useState(null);
  const [shareEmail, setShareEmail] = useState("");
  const [shareExpiryDate, setShareExpiryDate] = useState("");
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [generatePublicLink, setGeneratePublicLink] = useState(false);
  const [maxDownloads, setMaxDownloads] = useState("");
  const [publicLinkPassword, setPublicLinkPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [dateError, setDateError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [fileModalLoading, setFileModalLoading] = useState(false);
  const [publicLinks, setPublicLinks] = useState([]);
  const [linksLoading, setLinksLoading] = useState(false);

  // Fetch files on component mount
  useEffect(() => {
    const fetchFiles = async () => {
      if (!user || !user.id) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        console.log("Fetching files for user:", user.id);
        const response = await api.getUserFiles(user.id);
        console.log("API Response:", response);
        
        // Map API response to frontend format
        const mappedFiles = (response || []).map((file) => ({
          id: file.file_id,
          name: file.filename,
          owner: "You",
          lastAccessed: file.upload_date ? new Date(file.upload_date).toLocaleString() : "N/A",
          size: formatFileSize(file.size),
          uploadDate: file.upload_date ? new Date(file.upload_date).toLocaleDateString() : "N/A",
          hash: file.metadata?.hash || "N/A",
          encryption: file.metadata?.encryption || "AES-256",
          downloads: file.metadata?.downloads || 0,
          content_type: file.content_type
        }));
        
        console.log("Mapped files:", mappedFiles);
        setFiles(mappedFiles);
      } catch (err) {
        console.error("Failed to fetch files:", err);
        setError(err.message || "Failed to load files");
        setFiles([]);
      } finally {
        setLoading(false);
      }
    };

    fetchFiles();
  }, [user?.id]);

  let displayFiles = files;

  // Apply search in real-time
  if (searchQuery && searchQuery.length > 0) {
    const q = searchQuery.toLowerCase();
    displayFiles = displayFiles.filter((f) => f.name.toLowerCase().includes(q));
  }

  const handleDownloadFile = async (fileId, fileName) => {
    try {
      setFileModalLoading(true);
      const blob = await api.downloadFile(fileId);
      
      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
      
      // Close modal and refresh files
      setSelectedFile(null);
      // Optionally refresh the file list
    } catch (err) {
      console.error("Download failed:", err);
      setAlertMessage("Failed to download file: " + (err.message || "Unknown error"));
      setShowAlertModal(true);
    } finally {
      setFileModalLoading(false);
    }
  };

  const handleDeleteFile = async (fileId) => {
    try {
      setFileModalLoading(true);
      await api.deleteFile(fileId);
      
      // Remove the file from the list
      setFiles((prevFiles) => prevFiles.filter((f) => f.id !== fileId));
      setSelectedFile(null);
      
      setAlertMessage("File deleted successfully");
      setShowAlertModal(true);
    } catch (err) {
      console.error("Delete failed:", err);
      setAlertMessage("Failed to delete file: " + (err.message || "Unknown error"));
      setShowAlertModal(true);
    } finally {
      setFileModalLoading(false);
    }
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

  const handleCreateShareLink = async () => {
    // If generating public link, only expiry date is needed
    if (generatePublicLink) {
      let hasError = false;
      
      // Validate date (optional for public links)
      let expirationDate = null;
      if (shareExpiryDate) {
        if (!validateDate(shareExpiryDate)) {
          setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
          hasError = true;
        } else {
          setDateError("");
          // Parse date
          const parts = shareExpiryDate.split('/');
          let year = parseInt(parts[0]);
          const month = parseInt(parts[1]);
          const day = parseInt(parts[2]);
          
          if (parts[0].length === 2) {
            year += year < 50 ? 2000 : 1900;
          }
          
          expirationDate = new Date(year, month - 1, day).toISOString();
        }
      }
      
      if (hasError) return;

      try {
        setFileModalLoading(true);
        
        // Call API to create public link with optional password
        const response = await api.createShareLink(shareFile.id, expirationDate, publicLinkPassword || undefined);
        
        // The API returns link_url which already contains the full URL
        const publicLink = response.link_url || `${window.location.origin}/#/s/${response.token}/access`;
        
        setSuccessMessage(`✓ Public link created:\n${publicLink}`);
        // Don't auto-close - let user copy the link
        // setTimeout(() => {
        //   setShareFile(null);
        //   setSuccessMessage("");
        //   setShareEmail("");
        //   setShareExpiryDate("");
        //   setMaxDownloads("");
        //   setGeneratePublicLink(false);
        // }, 4000);
      } catch (err) {
        console.error("Public link creation failed:", err);
        setEmailError("Failed to create public link: " + (err.message || "Unknown error"));
      } finally {
        setFileModalLoading(false);
      }
      return;
    }
    
    // Otherwise, share with email
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
    
    // Validate date (optional)
    let expirationDate = null;
    if (shareExpiryDate) {
      if (!validateDate(shareExpiryDate)) {
        setDateError("Please enter a valid date (YY/MM/DD or YYYY/MM/DD)");
        hasError = true;
      } else {
        setDateError("");
        // Parse date
        const parts = shareExpiryDate.split('/');
        let year = parseInt(parts[0]);
        const month = parseInt(parts[1]);
        const day = parseInt(parts[2]);
        
        if (parts[0].length === 2) {
          year += year < 50 ? 2000 : 1900;
        }
        
        expirationDate = new Date(year, month - 1, day).toISOString();
      }
    }
    
    if (hasError) return;

    try {
      setFileModalLoading(true);
      
      // Call API to share file
      await api.shareFileWithUser(shareFile.id, shareEmail, expirationDate);
      
      setSuccessMessage(`✓ File shared with ${shareEmail}`);
      setTimeout(() => {
        setShareFile(null);
        setSuccessMessage("");
        setShareEmail("");
        setShareExpiryDate("");
      }, 2500);
    } catch (err) {
      console.error("Share failed:", err);
      setEmailError("Failed to share file: " + (err.message || "Unknown error"));
    } finally {
      setFileModalLoading(false);
    }
  };

  const handleShareFile = async (email, expiryDate) => {
    try {
      setFileModalLoading(true);
      
      // Call API to share file
      await api.shareFileWithUser(shareFile.id, email, expiryDate);
      
      setSuccessMessage(`✓ File shared with ${email}`);
      setTimeout(() => {
        setShareFile(null);
        setSuccessMessage("");
      }, 2500);
    } catch (err) {
      console.error("Share failed:", err);
      setAlertMessage("Failed to share file: " + (err.message || "Unknown error"));
      setShowAlertModal(true);
    } finally {
      setFileModalLoading(false);
    }
  };

  const handleShare = async (file) => {
    setShareFile(file);
    setShareEmail("");
    setShareExpiryDate("");
    setGeneratePublicLink(false);
    setMaxDownloads("");
    setPublicLinkPassword("");
    setEmailError("");
    setDateError("");
    setSuccessMessage("");
    
    // Fetch existing public links for this file
    try {
      setLinksLoading(true);
      const links = await api.getFilePublicLinks(file.id);
      setPublicLinks(links || []);
    } catch (err) {
      console.error("Failed to fetch public links:", err);
      setPublicLinks([]);
    } finally {
      setLinksLoading(false);
    }
  };

  const handleDeletePublicLink = async (linkId) => {
    try {
      await api.deletePublicLink(linkId);
      // Remove the deleted link from the list
      setPublicLinks(publicLinks.filter(link => link.id !== linkId));
      setSuccessMessage("✓ Public link deleted");
      setTimeout(() => setSuccessMessage(""), 2000);
    } catch (err) {
      console.error("Failed to delete public link:", err);
      setEmailError("Failed to delete link: " + (err.message || "Unknown error"));
    }
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

  useEffect(() => {
    function onToggle() { setMobileSidebarOpen(s => !s); }
    window.addEventListener("toggleMobileSidebar", onToggle);
    return () => window.removeEventListener("toggleMobileSidebar", onToggle);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileSidebarOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileSidebarOpen]);

  return (
    <>
      <TopNavBar>
        <style>{`
          .sidebar-btn { display:flex; align-items:center; justify-content:flex-start; width:100%; gap:0.3cm; height:2rem; font-size:0.875rem; padding:0.5rem 0.8rem; border-radius:0.5rem; outline:none; border:none; background-color:transparent; color:#64748b; font-weight:400; transition:all .2s ease; cursor:pointer; margin-bottom:0.6rem; }
          .sidebar-btn:hover { background-color:#f1f5f9; }
          .sidebar-btn.active { background-color:#e2e8f0; color:#0f172a; font-weight:500; }
          .file-link { color:#2563eb; text-decoration:underline; cursor:pointer; transition:opacity .2s; }
          .file-link:hover { opacity:0.7; }
          .modal-overlay { position:fixed; inset:0; background-color:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100; }
          .modal-content { background:#fff; border-radius:8px; padding:1.5rem; max-width:500px; width:90%; box-shadow:0 10px 40px rgba(0,0,0,0.15); }
          .modal-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; }
          .modal-title { font-size:1.25rem; font-weight:600; color:#0f172a; }
          .modal-close-btn { background:none; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; padding:0; }
          .modal-close-btn svg { color:#dc2626; width:1.5rem; height:1.5rem; }
          .modal-info { margin-bottom:1.5rem; }
          .modal-info-row { display:flex; justify-content:space-between; padding:0.5rem 0; border-bottom:1px solid #e5e7eb; font-size:0.875rem; }
          .modal-info-label { font-weight:500; color:#64748b; }
          .modal-info-value { color:#0f172a; }
          .modal-buttons { display:flex; gap:0.5rem; justify-content:flex-end; }
          .modal-btn { background-color:#2563eb; color:#fff; border:none; padding:0.5rem 1rem; border-radius:6px; cursor:pointer; font-weight:500; font-size:0.875rem; transition:background-color .2s; }
          .modal-btn:hover { background-color:#1d4ed8; }
          .search-wrapper { width:90%; max-width:90%; margin-left:0; }
          .content-width { width:90%; max-width:90%; margin-left:0; }
          .files-table { border:1px solid #e5e7eb; border-radius:8px; overflow:hidden; }
          .files-table > .table-inner { padding:0 0.5rem 0.5rem 0.5rem; }
          .files-table thead tr { border-bottom:1px solid #e5e7eb; }
          .files-table tbody tr { border-bottom:1px solid #e5e7eb; }
          .files-table th, .files-table td { padding-left:1rem; padding-right:1rem; }
          .files-table thead th { padding-top:0.45rem; padding-bottom:0.6rem; text-align:left; vertical-align:middle; }
          .files-table th:last-child, .files-table td:last-child { border-right:none; }
          .col-muted { color:#64748b; }
          .files-table .table-inner table { width:100%; }
          .share-input { width:100%; border:1px solid #d1d5db; border-radius:6px; padding:0.5rem 0.75rem; font-size:0.875rem; background:transparent; outline:none; transition:border-color .2s; height:2.5rem; }
          .share-input:focus { border-color:#2563eb; }
          .share-input-group { margin-bottom:1rem; position:relative; }
          .share-input-label { font-size:0.875rem; font-weight:500; color:#374151; margin-bottom:0.25rem; display:block; }
          .toggle-switch { display:inline-flex; align-items:center; width:48px; height:24px; background:#d1d5db; border-radius:12px; padding:2px; cursor:pointer; transition:background .2s; }
          .toggle-switch.active { background:#2563eb; }
          .toggle-switch-circle { width:20px; height:20px; background:white; border-radius:50%; transition:transform .2s; }
          .toggle-switch.active .toggle-switch-circle { transform:translateX(24px); }
          .share-modal-btn { width:100%; padding:0.5rem 1rem; border-radius:6px; font-size:0.875rem; font-weight:500; cursor:pointer; border:1px solid #d1d5db; background:transparent; color:#0f172a; transition:all .2s; height:2.5rem; }
          .share-modal-btn:hover { border-color:#9ca3af; }
          .share-modal-btn.primary { background:#2563eb; color:white; border:none; width:100%; }
          .share-modal-btn.primary:hover { background:#1d4ed8; }
          .calendar-icon-btn { position:absolute; right:0.75rem; top:50%; transform:translateY(-50%); background:none; border:none; cursor:pointer; padding:0; display:flex; align-items:center; justify-content:center; }
          .error-text { color:#dc2626; font-size:0.75rem; margin-top:0.25rem; display:block; }
          .mobile-menu { position:fixed; inset:0; background:rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:flex-end; z-index:60; }
          .panel { background:#fff; border-radius:8px; padding:1.5rem; width:320px; max-width:85%; box-shadow:-8px 0 24px rgba(0,0,0,0.12); }
        `}</style>

        {/* Sidebar (hide on small screens) */}
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
                className={`sidebar-btn ${idx === 1 ? "active" : ""}`}
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

        {/* Mobile sidebar panel for MyFiles */}
        {mobileSidebarOpen && (
          <div className="mobile-menu" onClick={() => setMobileSidebarOpen(false)} style={{ zIndex: 60 }}>
            <div className="panel" onClick={(e) => e.stopPropagation()} style={{ width: 320, maxWidth: "85%", boxShadow: "-8px 0 24px rgba(0,0,0,0.12)" }}>
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

          {/* Loading State */}
          {loading && (
            <div style={{
              textAlign: "center",
              padding: "3rem 1rem",
              color: "#64748b",
              fontSize: "1rem"
            }}>
              <p>Loading files...</p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div style={{
              backgroundColor: "#fee2e2",
              borderLeft: "4px solid #ef4444",
              padding: "1rem",
              borderRadius: "0.375rem",
              marginBottom: "1.5rem",
              color: "#991b1b"
            }}>
              <p style={{ margin: "0 0 0.5rem 0", fontWeight: "500" }}>Error loading files</p>
              <p style={{ margin: 0, fontSize: "0.875rem" }}>{error}</p>
            </div>
          )}

          {/* Files Table */}
          {!loading && (
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
                  {displayFiles.length === 0 && (
                    <tr>
                      <td colSpan="3" style={{ textAlign: "center", padding: "2rem", color: "#9ca3af" }}>
                        {searchQuery ? "No files match your search" : "You haven't uploaded any files yet. Go to Dashboard to upload files."}
                      </td>
                    </tr>
                  )}
                  {displayFiles.map((file) => (
                    <tr key={file.id} style={{ backgroundColor: "#ffffff", height: "2.75rem", borderBottom: displayFiles.indexOf(file) === displayFiles.length - 1 ? "none" : "1px solid #e5e7eb" }}>
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
          )}
        </main>

        {/* File Details Modal */}
        {selectedFile && !shareFile && (
          <FileDetailsModal
            file={selectedFile}
            onClose={() => setSelectedFile(null)}
            onDownload={(fileId, fileName) => {
              handleDownloadFile(fileId, fileName);
            }}
            onDelete={(fileId) => {
              handleDeleteFile(fileId);
            }}
            onShare={() => setShareFile(selectedFile)}
            loading={fileModalLoading}
          />
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
                {/* Email Input - Hidden when generating public link */}
                {!generatePublicLink && (
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
                )}

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

                {/* Password Input (only for public links) */}
                {generatePublicLink && (
                  <div className="share-input-group">
                    <label className="share-input-label">Password (optional)</label>
                    <input
                      type="password"
                      placeholder="Leave empty for no password"
                      value={publicLinkPassword}
                      onChange={(e) => setPublicLinkPassword(e.target.value)}
                      className="share-input"
                    />
                  </div>
                )}

                {/* Create Share Link Button */}
                <button className="share-modal-btn primary" onClick={handleCreateShareLink} disabled={fileModalLoading}>
                  {fileModalLoading ? "Creating..." : generatePublicLink ? "Create public link" : "Create share link"}
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
                  <div style={{
                    marginTop: "1.5rem",
                    paddingTop: "1rem",
                    borderTop: "1px solid #e5e7eb"
                  }}>
                    <h3 style={{
                      fontSize: "0.875rem",
                      fontWeight: 600,
                      color: "#374151",
                      marginBottom: "0.75rem",
                      margin: 0
                    }}>
                      Existing Public Links
                    </h3>
                    <div style={{
                      marginTop: "0.75rem",
                      display: "flex",
                      flexDirection: "column",
                      gap: "0.5rem"
                    }}>
                      {publicLinks.map((link) => (
                        <div
                          key={link.id}
                          style={{
                            padding: "0.75rem",
                            backgroundColor: "#f9fafb",
                            border: "1px solid #e5e7eb",
                            borderRadius: "6px",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "space-between",
                            fontSize: "0.75rem"
                          }}
                        >
                          <div style={{ flex: 1, minWidth: 0 }}>
                            <div style={{
                              color: "#0f172a",
                              whiteSpace: "nowrap",
                              overflow: "hidden",
                              textOverflow: "ellipsis",
                              fontFamily: "monospace",
                              marginBottom: "0.25rem"
                            }}>
                              {link.short_code ? `${window.location.origin}/#/s/${link.short_code}/access` : "Link"}
                            </div>
                            <div style={{ color: "#64748b" }}>
                              Created: {new Date(link.created_at).toLocaleDateString()}
                              {link.expires_at && ` | Expires: ${new Date(link.expires_at).toLocaleDateString()}`}
                            </div>
                          </div>
                          <button
                            onClick={() => handleDeletePublicLink(link.id)}
                            style={{
                              marginLeft: "0.5rem",
                              padding: "0.4rem 0.6rem",
                              backgroundColor: "#fee2e2",
                              color: "#dc2626",
                              border: "none",
                              borderRadius: "4px",
                              cursor: "pointer",
                              fontSize: "0.7rem",
                              fontWeight: 500,
                              whiteSpace: "nowrap",
                              transition: "all 0.2s"
                            }}
                            onMouseEnter={(e) => {
                              e.target.style.backgroundColor = "#fecaca";
                            }}
                            onMouseLeave={(e) => {
                              e.target.style.backgroundColor = "#fee2e2";
                            }}
                          >
                            Delete
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </TopNavBar>

      {showAlertModal && (
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
            zIndex: 1000
          }}
          onClick={() => setShowAlertModal(false)}
        >
          <div
            style={{
              backgroundColor: "white",
              padding: "2rem",
              borderRadius: "8px",
              maxWidth: "400px",
              textAlign: "center",
              boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)"
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <p style={{ marginTop: 0, marginBottom: "1.5rem", color: "#333" }}>
              {alertMessage}
            </p>
            <button
              onClick={() => setShowAlertModal(false)}
              style={{
                padding: "0.75rem 1.5rem",
                backgroundColor: "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: "6px",
                cursor: "pointer",
                fontSize: "1rem"
              }}
            >
              OK
            </button>
          </div>
        </div>
      )}
    </>
  );
}

// Utility function to format file size
function formatFileSize(bytes) {
  if (!bytes || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB", "TB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return (Math.round((bytes / Math.pow(k, i)) * 10) / 10) + " " + sizes[i];
}
