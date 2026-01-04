import React, { useState, useEffect } from "react";
import { Calendar, X } from "lucide-react";
import { useNavigate } from "react-router-dom";
import TopNavBar from "../../layout/TopNavBar";
import { api } from "../../services/api";
import { useAuth } from "../../hooks/useAuth";
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

export default function Shared() {
  const routerNavigate = useNavigate();
  const { user } = useAuth();
  const [extendFile, setExtendFile] = useState(null);
  const [extendDate, setExtendDate] = useState("");
  const [showCalendar, setShowCalendar] = useState(false);
  const [calendarDate, setCalendarDate] = useState(new Date());
  const [dateError, setDateError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [showAlertModal, setShowAlertModal] = useState(false);
  const [alertMessage, setAlertMessage] = useState("");
  const [sharedByMe, setSharedByMe] = useState([]);
  const [sharedWithMe, setSharedWithMe] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    function onToggle() { setMobileSidebarOpen(s => !s); }
    window.addEventListener("toggleMobileSidebar", onToggle);
    return () => window.removeEventListener("toggleMobileSidebar", onToggle);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileSidebarOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileSidebarOpen]);

  // Fetch shared files
  useEffect(() => {
    const fetchSharedFiles = async () => {
      if (!user || !user.id) {
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        setError(null);

        // Fetch files shared by me
        const byMeResponse = await api.getSharedByMe(user.id);
        const processedByMe = await Promise.all((byMeResponse || []).map(async (share) => {
          let userEmail = "Unknown";
          try {
            const userInfo = await api.getCurrentUser(share.shared_with_user_id);
            userEmail = userInfo.email || "Unknown";
          } catch (err) {
            console.error("Failed to fetch user info:", err);
          }
          
          return {
            id: share.share_id,
            share_id: share.share_id,
            file_id: share.file_id,
            name: share.file_name || `File (${share.file_id.substring(0, 8)})`,
            sharedWith: userEmail,
            status: share.expires_at && new Date(share.expires_at) < new Date() ? "Expired" : "Active",
            expiration: share.expires_at ? new Date(share.expires_at).toLocaleDateString() : "Never",
            direction: "by_me"
          };
        }));

        // Fetch files shared with me
        const withMeResponse = await api.getSharedWithMe(user.id);
        const processedWithMe = await Promise.all((withMeResponse || []).map(async (share) => {
          let userEmail = "Unknown";
          try {
            const userInfo = await api.getCurrentUser(share.shared_by_user_id);
            userEmail = userInfo.email || "Unknown";
          } catch (err) {
            console.error("Failed to fetch user info:", err);
          }
          
          return {
            id: share.share_id,
            share_id: share.share_id,
            file_id: share.file_id,
            name: share.file_name || `File (${share.file_id.substring(0, 8)})`,
            sharedWith: userEmail,
            status: share.expires_at && new Date(share.expires_at) < new Date() ? "Expired" : "Active",
            expiration: share.expires_at ? new Date(share.expires_at).toLocaleDateString() : "Never",
            direction: "with_me"
          };
        }));

        setSharedByMe(processedByMe);
        setSharedWithMe(processedWithMe);
      } catch (err) {
        console.error("Failed to fetch shared files:", err);
        setError(err.message || "Failed to load shared files");
        setSharedByMe([]);
        setSharedWithMe([]);
      } finally {
        setLoading(false);
      }
    };

    fetchSharedFiles();
  }, [user?.id]);

  const handleRevoke = async (file) => {
    try {
      await api.revokeFileShare(file.share_id);
      
      // Remove from shared by me list
      setSharedByMe(prev => prev.filter(f => f.share_id !== file.share_id));
      
      setAlertMessage(`✓ Successfully revoked access to "${file.name}"`);
      setShowAlertModal(true);
    } catch (err) {
      console.error("Revoke failed:", err);
      setAlertMessage("Failed to revoke: " + (err.message || "Unknown error"));
      setShowAlertModal(true);
    }
  };

  const handleDownload = async (file) => {
    try {
      const blob = await api.downloadFile(file.file_id);
      
      // Create a download link
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = file.name || `file_${file.file_id.substring(0, 8)}`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
      setAlertMessage("Failed to download: " + (err.message || "Unknown error"));
      setShowAlertModal(true);
    }
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

  const handleExtend = (file) => {
    setExtendFile(file);
    setExtendDate("");
    setDateError("");
    setShowCalendar(false);
  };

  const handleCalendarDateSelect = (day, month, year) => {
    const dateStr = `${String(year).slice(-2)}/${String(month + 1).padStart(2, '0')}/${String(day).padStart(2, '0')}`;
    setExtendDate(dateStr);
    setShowCalendar(false);
  };

  const handleConfirmExtend = () => {
    if (!extendDate) {
      setDateError("Date is required");
      return;
    }
    if (!validateDate(extendDate)) {
      setDateError("Please enter a valid date (YY/MM/DD)");
      return;
    }
    setSuccessMessage(`✓ Successfully extended ${extendFile.name} until ${extendDate}`);
    setTimeout(() => {
      setExtendFile(null);
      setSuccessMessage("");
    }, 2500);
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

  const SharedTable = ({ title, data, isSharedByMe = false }) => (
    <div style={{ marginBottom: "2rem" }}>
      <h3 style={{ fontSize: "1.125rem", fontWeight: "600", color: "#0f172a", marginBottom: "1rem" }}>{title}</h3>
      <div className="shared-table" style={{ border: "1px solid #e5e7eb", borderRadius: "8px" }}>
        <div className="table-inner" style={{ width: "100%", overflowX: "auto", WebkitOverflowScrolling: "touch" }}>
          <table style={{ width: "100%", textAlign: "left", borderCollapse: "collapse", minWidth: "720px", tableLayout: "auto" }}>
           <colgroup>
             <col style={{ width: "25%" }} />
             <col style={{ width: "25%" }} />
             <col style={{ width: "15%" }} />
             <col style={{ width: "20%" }} />
             <col style={{ width: "15%" }} />
           </colgroup>
           <thead>
             <tr style={{ backgroundColor: "transparent", borderBottom: "1px solid #e5e7eb" }}>
               <th style={{ padding: "1rem", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Name</th>
               <th style={{ padding: "1rem", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>{isSharedByMe ? "Shared With" : "Shared By"}</th>
               <th style={{ padding: "1rem", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Status</th>
               <th style={{ padding: "1rem", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Expiration</th>
               <th style={{ padding: "1rem", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>Actions</th>
             </tr>
           </thead>
           <tbody>
             {data.map((file) => (
               <tr key={file.id} style={{ backgroundColor: "#ffffff", height: "2.75rem", borderBottom: "1px solid #e5e7eb" }}>
                 <td style={{ padding: "1rem", fontSize: "0.875rem", color: "#0f172a", whiteSpace: "nowrap" }}>{file.name}</td>
                 <td style={{ padding: "1rem", fontSize: "0.875rem", color: "#64748b", whiteSpace: "nowrap" }}>{file.sharedWith}</td>
                 <td style={{ padding: "1rem", fontSize: "0.875rem", color: "#64748b" }}>
                   <span style={{ padding: "0.25rem 0.5rem", borderRadius: "4px", backgroundColor: file.status === "Active" ? "#dcfce7" : "#fee2e2", color: file.status === "Active" ? "#166534" : "#991b1b" }}>
                     {file.status}
                   </span>
                 </td>
                 <td style={{ padding: "1rem", fontSize: "0.875rem", color: "#64748b", whiteSpace: "nowrap" }}>{file.expiration}</td>
                 <td style={{ padding: "1rem" }}>
                   <div style={{ display: "flex", gap: "0.5rem" }}>
                     <button
                       onClick={() => handleDownload(file)}
                       style={{
                         padding: "0.4rem 0.75rem",
                         borderRadius: "6px",
                         border: "1px solid #d1d5db",
                         backgroundColor: "#f3f4f6",
                         color: "#000000",
                         fontSize: "0.875rem",
                         cursor: "pointer",
                       }}
                     >
                       Download
                     </button>
                     {file.status === "Active" ? (
                       <button
                         onClick={() => handleRevoke(file)}
                         style={{
                           padding: "0.4rem 0.75rem",
                           borderRadius: "6px",
                           border: "1px solid #d1d5db",
                           backgroundColor: "#f3f4f6",
                           color: "#000000",
                           fontSize: "0.875rem",
                           cursor: "pointer",
                         }}
                       >
                         Revoke
                       </button>
                     ) : (
                       <button
                         onClick={() => handleExtend(file)}
                         style={{
                           padding: "0.4rem 0.75rem",
                           borderRadius: "6px",
                           border: "1px solid #d1d5db",
                           backgroundColor: "#f3f4f6",
                           color: "#000000",
                           fontSize: "0.875rem",
                           cursor: "pointer",
                         }}
                       >
                         Extend
                       </button>
                     )}
                   </div>
                 </td>
               </tr>
             ))}
           </tbody>
         </table>
       </div>
     </div>
   </div>
 );

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

        /* Allow horizontal scrolling for shared tables without changing columns */
        .shared-table .table-inner { overflow-x: auto; -webkit-overflow-scrolling: touch; }
        .shared-table table { min-width: 720px; table-layout: auto; }
        .shared-table th, .shared-table td { white-space: nowrap; }

        .modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background-color: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 100; }
        .modal-content { background: #ffffff; border-radius: 8px; padding: 1.5rem; max-width: 500px; width: 90%; box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15); }
        .modal-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
        .modal-title { font-size: 1.25rem; font-weight: 600; color: #0f172a; }
        .modal-close-btn { background: none; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; padding: 0; }
        .modal-close-btn svg { color: #dc2626; width: 1.5rem; height: 1.5rem; }
        .error-text { color: #dc2626; font-size: 0.75rem; margin-top: 0.25rem; display: block; }
        .share-input { width: 100%; border: 1px solid #d1d5db; border-radius: 6px; padding: 0.5rem 0.75rem; font-size: 0.875rem; background: transparent; outline: none; transition: border-color 0.2s; height: 2.5rem; }
        .share-input:focus { border-color: #2563eb; }
        .share-input-group { margin-bottom: 1rem; position: relative; }
        .share-input-label { font-size: 0.875rem; font-weight: 500; color: #374151; margin-bottom: 0.25rem; display: block; }
        .calendar-icon-btn { position: absolute; right: 0.75rem; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer; padding: 0; display: flex; align-items: center; justify-content: center; }
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
              className={`sidebar-btn ${idx === 2 ? "active" : ""}`}
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
          <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "#0f172a" }}>Shared with Me</h1>
        </header>

        {/* Loading State */}
        {loading && (
          <div style={{
            textAlign: "center",
            padding: "3rem 1rem",
            color: "#64748b",
            fontSize: "1rem"
          }}>
            <p>Loading shared files...</p>
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
            <p style={{ margin: "0 0 0.5rem 0", fontWeight: "500" }}>Error loading shared files</p>
            <p style={{ margin: 0, fontSize: "0.875rem" }}>{error}</p>
          </div>
        )}

        {/* Shared by Me Section */}
        {!loading && (
          <section style={{ marginBottom: "4rem" }}>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>Shared by Me</h2>
            {sharedByMe.length === 0 ? (
              <div style={{ textAlign: "center", padding: "2rem", color: "#9ca3af" }}>
                No files shared yet
              </div>
            ) : (
              <SharedTable title="Active Shares" data={sharedByMe.filter(f => !f.isExpired)} isSharedByMe={true} onExtend={handleExtend} />
            )}
          </section>
        )}

        {/* Shared with Me Section */}
        {!loading && (
          <section>
            <h2 style={{ fontSize: "1.5rem", fontWeight: "bold", color: "#0f172a", marginBottom: "1.5rem" }}>Shared with Me</h2>
            {sharedWithMe.length === 0 ? (
              <div style={{ textAlign: "center", padding: "2rem", color: "#9ca3af" }}>
                No files shared with you
              </div>
            ) : (
              <SharedTable title="Shared Files" data={sharedWithMe} isSharedByMe={false} onExtend={handleExtend} />
            )}
          </section>
        )}
      </main>

      {/* Extend Modal */}
      {extendFile && (
        <div className="modal-overlay" onClick={() => setExtendFile(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Extend "{extendFile.name}"</h2>
              <button className="modal-close-btn" onClick={() => setExtendFile(null)}>
                <X />
              </button>
            </div>

            <div style={{ marginBottom: "1.5rem" }}>
              <div className="share-input-group">
                <label className="share-input-label">Extend Until</label>
                <div style={{ position: "relative" }}>
                  <input
                    type="text"
                    placeholder="YY/MM/DD"
                    value={extendDate}
                    onChange={(e) => {
                      setExtendDate(e.target.value);
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

              <button
                onClick={handleConfirmExtend}
                style={{
                  width: "100%",
                  backgroundColor: "#2563eb",
                  color: "#ffffff",
                  border: "none",
                  padding: "0.75rem",
                  borderRadius: "6px",
                  fontSize: "0.875rem",
                  fontWeight: "600",
                  cursor: "pointer",
                }}
              >
                Confirm Extend
              </button>
              {successMessage && (
                <div style={{
                  marginTop: "1rem",
                  padding: "0.75rem",
                  backgroundColor: "#dcfce7",
                  color: "#166534",
                  borderRadius: "6px",
                  fontSize: "0.875rem",
                  textAlign: "center",
                  border: "1px solid #bbf7d0"
                }}>
                  {successMessage}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

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
    </TopNavBar>
  );
}
