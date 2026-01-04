import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { X, Link } from "lucide-react";
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
  { icon: null, label: "Public Links", to: "/public-links", lucideIcon: "Link" },
  { icon: TrashIcon, label: "Trash", to: "/trash" },
  { icon: SettingsIcon, label: "Settings", to: "/settings" },
];

const SAMPLE_TRASH = [
  { id: 1, name: "VacationPhotos.zip", originalLocation: "My Files/Pictures", dateDeleted: "2025-12-24", size: "50 MB" },
  { id: 2, name: "OldProject.pdf", originalLocation: "My Files/Documents", dateDeleted: "2025-12-20", size: "8.3 MB" },
  { id: 3, name: "BackupData.xlsx", originalLocation: "My Files/Archive", dateDeleted: "2025-12-18", size: "12.7 MB" },
  { id: 4, name: "TempVideo.mp4", originalLocation: "My Files/Videos", dateDeleted: "2025-12-15", size: "120 MB" },
];

export default function Trash() {
  const routerNavigate = useNavigate();
  const [deletedFiles, setDeletedFiles] = useState(SAMPLE_TRASH);
  const [actionStates, setActionStates] = useState({}); // Track clicked actions
  const [deleteWarning, setDeleteWarning] = useState(null); // Track delete warning modal
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  useEffect(() => {
    function onToggle() { setMobileSidebarOpen(s => !s); }
    window.addEventListener("toggleMobileSidebar", onToggle);
    return () => window.removeEventListener("toggleMobileSidebar", onToggle);
  }, []);

  useEffect(() => {
    document.body.style.overflow = mobileSidebarOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [mobileSidebarOpen]);

  const handleRestore = (fileId) => {
    setActionStates(prev => ({ ...prev, [fileId]: "restored" }));
    setTimeout(() => {
      setDeletedFiles(prev => prev.filter(f => f.id !== fileId));
      setActionStates(prev => {
        const newState = { ...prev };
        delete newState[fileId];
        return newState;
      });
    }, 1500);
  };

  const handlePermanentlyDelete = (fileId) => {
    setDeleteWarning(fileId);
  };

  const confirmPermanentDelete = () => {
    if (deleteWarning) {
      setActionStates(prev => ({ ...prev, [deleteWarning]: "deleted" }));
      setTimeout(() => {
        setDeletedFiles(prev => prev.filter(f => f.id !== deleteWarning));
        setActionStates(prev => {
          const newState = { ...prev };
          delete newState[deleteWarning];
          return newState;
        });
        setDeleteWarning(null);
      }, 1500);
    }
  };

  const cancelPermanentDelete = () => {
    setDeleteWarning(null);
  };

  const SharedTable = ({ title, data }) => (
    <div style={{ marginBottom: "2rem" }}>
      <h3 style={{ fontSize: "1.125rem", fontWeight: 600, color: "#0f172a", marginBottom: "1rem" }}>{title}</h3>
      <div className="trash-table" style={{ border: "1px solid #e5e7eb", borderRadius: "8px", padding: "1rem" }}>
        <div className="table-inner overflow-x-auto" style={{ width: "100%", WebkitOverflowScrolling: "touch" }}>
          <table style={{ width: "100%", textAlign: "left", borderCollapse: "collapse", minWidth: "700px" }}>
            <colgroup>
              <col style={{ width: "25%" }} />
              <col style={{ width: "25%" }} />
              <col style={{ width: "15%" }} />
              <col style={{ width: "20%" }} />
              <col style={{ width: "15%" }} />
            </colgroup>
            <thead>
              <tr style={{ backgroundColor: "transparent", borderBottom: "1px solid #e5e7eb" }}>
                <th style={{ padding: "1rem 0", fontSize: "0.875rem", fontWeight: 600, color: "#374151", textAlign: "left", verticalAlign: "top" }}>Name</th>
                <th style={{ padding: "1rem 0", fontSize: "0.875rem", fontWeight: 600, color: "#374151", textAlign: "left", verticalAlign: "top" }}>Original Location</th>
                <th style={{ padding: "1rem 0", fontSize: "0.875rem", fontWeight: 600, color: "#374151", textAlign: "left", verticalAlign: "top" }}>Date Deleted</th>
                <th style={{ padding: "1rem 0", fontSize: "0.875rem", fontWeight: 600, color: "#374151", textAlign: "left", verticalAlign: "top" }}>Size</th>
                <th style={{ padding: "1rem 0", fontSize: "0.875rem", fontWeight: 600, color: "#374151", textAlign: "left", verticalAlign: "top" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {data.map((file, idx) => (
                <tr key={file.id} style={{ backgroundColor: "#ffffff", borderBottom: idx === data.length - 1 ? "none" : "1px solid #e5e7eb" }}>
                  <td style={{ padding: "1rem 0", fontSize: "0.875rem", color: "#0f172a", verticalAlign: "top" }}>{file.name}</td>
                  <td style={{ padding: "1rem 0", fontSize: "0.875rem", color: "#64748b", verticalAlign: "top" }}>{file.originalLocation}</td>
                  <td style={{ padding: "1rem 0", fontSize: "0.875rem", color: "#64748b", verticalAlign: "top" }}>{file.dateDeleted}</td>
                  <td style={{ padding: "1rem 0", fontSize: "0.875rem", color: "#64748b", verticalAlign: "top" }}>{file.size}</td>
                  <td style={{ padding: "1rem 0", verticalAlign: "top" }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem" }}>
                      <span
                        onClick={() => handleRestore(file.id)}
                        style={{ 
                          color: actionStates[file.id] === "restored" ? "#16a34a" : "#2563eb",
                          textDecoration: "underline",
                          cursor: "pointer",
                          fontWeight: 500,
                          fontSize: "0.875rem",
                          transition: "all 0.2s"
                        }}
                      >
                        {actionStates[file.id] === "restored" ? "✓ Restored" : "Restore"}
                      </span>
                      <span
                        onClick={() => handlePermanentlyDelete(file.id)}
                        style={{
                          color: actionStates[file.id] === "deleted" ? "#dc2626" : "#2563eb",
                          textDecoration: "underline",
                          cursor: "pointer",
                          fontWeight: 500,
                          fontSize: "0.875rem",
                          transition: "all 0.2s"
                        }}
                      >
                        {actionStates[file.id] === "deleted" ? "✓ Deleted" : "Permanently Delete"}
                      </span>
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
        .sidebar-btn { display:flex; align-items:center; justify-content:flex-start; width:100%; gap:0.3cm; height:2rem; font-size:0.875rem; padding:0.5rem 0.8rem; border-radius:0.5rem; outline:none; border:none; background-color:transparent; color:#64748b; font-weight:400; transition:all .2s ease; cursor:pointer; margin-bottom:0.6rem; }
        .sidebar-btn:hover { background-color:#f1f5f9; }
        .sidebar-btn.active { background-color:#e2e8f0; color:#0f172a; font-weight:500; }

        .trash-table { border:1px solid #e5e7eb; border-radius:8px; width:90%; max-width:90%; }
        .trash-table .table-inner { overflow-x: auto; -webkit-overflow-scrolling: touch; }
        .trash-table table { width:100%; border-collapse:collapse; min-width:700px; table-layout: auto; }
        .trash-table th, .trash-table td { white-space: nowrap; }

        .action-link { color:#2563eb; text-decoration:underline; cursor:pointer; margin-right:1rem; transition:all .2s; font-weight:500; }
        .action-link:hover { opacity:0.7; }
        .action-link.restored { color:#16a34a; }
        .action-link.deleted { color:#dc2626; }

        .modal-overlay { position:fixed; inset:0; background-color:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; z-index:100; }
        .modal-content { background:#fff; border-radius:8px; padding:1.5rem; max-width:400px; width:90%; box-shadow:0 10px 40px rgba(0,0,0,0.15); }
        .modal-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:1rem; }
        .modal-title { font-size:1.25rem; font-weight:600; color:#0f172a; }
        .modal-close-btn { background:none; border:none; cursor:pointer; display:flex; align-items:center; justify-content:center; padding:0; }
        .modal-close-btn svg { color:#dc2626; width:1.5rem; height:1.5rem; }
        .modal-text { font-size:0.875rem; color:#64748b; margin-bottom:1.5rem; line-height:1.6; }
        .warning-text { color:#dc2626; font-weight:600; }
        .modal-buttons { display:flex; gap:0.75rem; justify-content:flex-end; }
        .modal-btn { padding:0.5rem 1rem; border-radius:6px; cursor:pointer; font-weight:500; font-size:0.875rem; border:none; transition:background-color 0.2s; }
        .modal-btn-cancel { background-color:#e5e7eb; color:#0f172a; }
        .modal-btn-cancel:hover { background-color:#d1d5db; }
        .modal-btn-delete { background-color:#dc2626; color:#fff; }
        .modal-btn-delete:hover { background-color:#b91c1c; }

        .mobile-menu { position:fixed; inset:0; background:rgba(0,0,0,0.7); display:flex; align-items:center; justify-content:center; z-index:60; }
        .panel { background:#fff; border-radius:8px; padding:1.5rem; max-width:400px; width:90%; box-shadow:0 10px 40px rgba(0,0,0,0.15); }
        .panel strong { font-size:1.25rem; font-weight:600; color:#0f172a; display:block; margin-bottom:1rem; }
        .panel button { background:none; border:none; cursor:pointer; padding:0; font-size:1.5rem; color:#dc2626; }
        .panel nav { display:flex; flex-direction:column; gap:0.6rem; }
        .panel nav button { display:flex; gap:0.5rem; align-items:center; padding:0.6rem 0.2rem; background:transparent; border:none; cursor:pointer; font-size:0.875rem; color:#0f172a; transition:background-color 0.2s; }
        .panel nav button:hover { background-color:#f1f5f9; }
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
          <h1 style={{ fontSize: "2rem", fontWeight: "bold", color: "#0f172a", marginBottom: "0.5rem" }}>
            Deleted Files
          </h1>
          <p style={{ fontSize: "0.75rem", color: "#64748b" }}>
            Files in your trash will be automatically deleted after 30 days.
          </p>
        </header>

        {/* Trash Table */}
        {deletedFiles.length > 0 ? (
          <SharedTable title="Deleted Files" data={deletedFiles} />
        ) : (
          <div style={{ textAlign: "center", padding: "3rem", color: "#64748b" }}>
            <p>Your trash is empty.</p>
          </div>
        )}
      </main>

      {/* Delete Confirmation Modal */}
      {deleteWarning && (
        <div className="modal-overlay" onClick={cancelPermanentDelete}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="modal-title">Permanently Delete File?</h2>
              <button className="modal-close-btn" onClick={cancelPermanentDelete}>
                <X />
              </button>
            </div>

            <div className="modal-text">
              Are you sure you want to <span className="warning-text">permanently delete</span> this file? This action cannot be undone.
            </div>

            <div className="modal-buttons">
              <button className="modal-btn modal-btn-cancel" onClick={cancelPermanentDelete}>
                No, Cancel
              </button>
              <button className="modal-btn modal-btn-delete" onClick={confirmPermanentDelete}>
                Yes, Delete Permanently
              </button>
            </div>
          </div>
        </div>
      )}
    </TopNavBar>
  );
}
